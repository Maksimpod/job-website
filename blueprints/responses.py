import random

from flask import Blueprint, render_template, redirect, request, url_for
from datamodels import VacancyResponses, Vacancies, Companies, Users
from flask_login import current_user
from lib import db, utility

import sqlalchemy as sa

import datetime

responses = Blueprint('responses', __name__, template_folder='templates', url_prefix='/responses')


@responses.route('/')
def responsesPageRoute():
  session = db.getDBSession()

  if not current_user.is_authenticated:
    return redirect("/login")

  userId = current_user.get_id()

  user = session.scalar(
    sa.select(Users).where(Users.id == userId))

  if user.roleId != 3:
    return redirect("/")

  responses_data = session.execute(
    sa.select(VacancyResponses, Vacancies, Companies)
    .join(Vacancies, VacancyResponses.vacancyId == Vacancies.id)
    .join(Companies, Vacancies.companyId == Companies.id)
    .where(VacancyResponses.userId == int(current_user.get_id()))
    .order_by(VacancyResponses.created.desc())
  ).all()

  return render_template('responses.html', responses=responses_data, format_date=utility.format_date)


def generate_responses(session):
  try:
    vacancy_ids = [56, 757, 973, 1402, 1501]
    user_ids = list(range(1, 1019))

    for vacancy_id in vacancy_ids:
      selected_users = random.sample(user_ids, 30)
      selected_users.append(1021)
      for user_id in selected_users:
        response = VacancyResponses(
          vacancyId=vacancy_id,
          userId=user_id,
          created=datetime.datetime.now(),
        )

        session.add(response)

    session.commit()

  except Exception as e:
    session.rollback()
    print(f"Ошибка: {e}")


@responses.route('/update-response-status', methods=['POST'])
def update_response_status():
    if not current_user.is_authenticated:
        return redirect("/login")

    vacancy_id = request.form.get('vacancy_id')
    user_id = request.form.get('user_id')
    new_status = request.form.get('new_status')

    if int(user_id) != int(current_user.get_id()):
        return redirect(url_for('responses.responsesPageRoute'))

    session = db.getDBSession()
    try:
        session.execute(
            sa.update(VacancyResponses)
            .where(VacancyResponses.vacancyId == vacancy_id)
            .where(VacancyResponses.userId == user_id)
            .values(status=new_status)
        )
        session.commit()
    except Exception as e:
        session.rollback()
        print(f'Ошибка: {str(e)}', 'error')
    finally:
        session.close()

    return redirect(url_for('responses.responsesPageRoute'))

