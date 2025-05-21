from flask import Blueprint, render_template, redirect, request, url_for
from sqlalchemy import select

from datamodels import VacancyResponses, Vacancies, Companies, Users, Resumes, Workplaces, t_resumeWorkplaces
from flask_login import current_user
from lib import db, utility

import sqlalchemy as sa

candidates = Blueprint('candidates', __name__, template_folder='templates', url_prefix='/candidates')


@candidates.route('/')
def candidatesPageRoute():
  session = db.getDBSession()

  if not current_user.is_authenticated:
    return redirect("/login")

  userId = current_user.get_id()

  user = session.scalar(
    sa.select(Users).where(Users.id == userId))

  if user.roleId != 2:
    return redirect("/")

  responses_data = session.execute(
    sa.select(Resumes, VacancyResponses, Vacancies, Users)
    .join(Users, Resumes.userId == Users.id)
    .join(VacancyResponses, VacancyResponses.userId == Users.id)
    .join(Vacancies, VacancyResponses.vacancyId == Vacancies.id)
    .join(Companies, Vacancies.companyId == Companies.id)
    .where(Companies.userId == current_user.id)
    .order_by(VacancyResponses.created.desc())
  ).all()

  result = []
  for resume, response, vacancy, user in responses_data:
    workplaces = session.execute(
      sa.select(Workplaces)
      .join(t_resumeWorkplaces, Workplaces.id == t_resumeWorkplaces.c.workplaceId)
      .where(t_resumeWorkplaces.c.resumeId == resume.id)
      .order_by(
        Workplaces.endYear.is_(None).desc(),
        Workplaces.endYear.desc(),
        Workplaces.beginYear.desc()
      )
    ).scalars().all()

    result.append({
      'resume': resume,
      'response': response,
      'vacancy': vacancy,
      'user': user,
      'workplaces': workplaces
    })

  return render_template('candidates.html', responses=result, format_date=utility.format_date, utility=utility)


@candidates.route('/update-response-status', methods=['POST'])
def cupdate_response_status():
  if not current_user.is_authenticated:
    return redirect("/login")

  vacancy_id = request.form.get('vacancy_id')
  user_id = request.form.get('user_id')
  new_status = request.form.get('new_status')

  session = db.getDBSession()
  response = session.execute(select(VacancyResponses)
        .where(VacancyResponses.vacancyId == vacancy_id)
        .where(VacancyResponses.userId == user_id)).scalar_one_or_none()

  if not response:
    return redirect(url_for('candidates.candidatesPageRoute'))

  try:
    response.status = int(new_status)
    session.commit()
  except Exception as e:
    session.rollback()
    print(f'Ошибка: {str(e)}', 'error')
  finally:
    session.close()

  return redirect(url_for('candidates.candidatesPageRoute'))
