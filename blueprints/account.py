from flask import Blueprint, render_template, current_app, request, flash, redirect
from flask_login import current_user, login_user, logout_user
from sqlalchemy import select

from forms import RegisterForm, LoginForm, SearchMainForm
import sqlalchemy as sa

from datamodels import Users, Resumes, Vacancies, Companies

from lib import db
from lib import searchFunc

import sys, datetime, urllib, re

sys.path.append('../blocks')

from blocks import numerator


itemsPerPage = 20

account = Blueprint('account', __name__, template_folder='templates', url_prefix=None)


@account.route('/account_page')
@db.cache.cached(query_string=True)
def accountPageRoute():
  if not current_user.is_authenticated:
    return redirect('/login')

  session = db.getDBSession()

  if current_user.roleId == 3:
    form = SearchMainForm()

    sortBy = 'date'
    sortOrder = 'desc'
    searchText = ''

    resumes = session.execute(sa.select(Resumes).where(Resumes.userId == current_user.id)).scalars().all()

    for resume in resumes:
      if (resume.position != ''):
        resumePositionWords = resume.position.split(' ')

        if (len(resumePositionWords) > 2):
          resumePositionWords = resumePositionWords[0:2]

        if (len(resumePositionWords) >= 1):
          searchText = resumePositionWords[0].strip().lower()

        if (len(resumePositionWords) >= 2):
          searchText += ' ' + resumePositionWords[1].strip().lower()

      if (searchText != ''):
        break


    pageURLArgName = 'page'
    page = int(request.args.get(pageURLArgName, 1))

    if (page < 1):
      page = 1

    limit = itemsPerPage
    offset = (page - 1) * itemsPerPage

    searchVacanciesCount = searchFunc.doSearch('vacancies', 'title', searchText, offset, limit, sortOrder, sortBy, True)
    searchResult = searchFunc.doSearch('vacancies', 'title', searchText, offset, limit, sortOrder, sortBy)

    for searchResultItem in searchResult:
      if (('vacancy' in searchResultItem) and isinstance(searchResultItem['vacancy'], dict)):
        if ('created' in searchResultItem['vacancy']):
          searchResultItem['vacancy']['created'] = datetime.datetime.strptime(searchResultItem['vacancy']['created'], '%Y.%m.%d %H:%M:%S')
        if ('description' in searchResultItem['vacancy']):
          searchResultItem['vacancy']['description'] = re.sub(r"<[^>]*?>", ' ', str(searchResultItem['vacancy']['description']))

    requestArgs = request.args.to_dict()

    if (pageURLArgName in requestArgs):
      del requestArgs[pageURLArgName]

    requestArgs['page'] = ''

    paginationURLPrefix = urllib.parse.urlencode(requestArgs)
    paginationBaseURL = request.url_rule.rule

    if (paginationBaseURL.endswith('/')):
      paginationBaseURL = paginationBaseURL[:-1]

    pagesTotal = int(searchVacanciesCount / itemsPerPage)

    if (searchVacanciesCount % itemsPerPage > 0):
      pagesTotal += 1

    pageNumeratorHTML = numerator.NumeratorBlock.create({
      'currentPage': page,
      'pagesTotal': pagesTotal,
      'baseURL': paginationBaseURL,
      'pageNumberPrefix': f"?{paginationURLPrefix}"
    })

    return render_template('account_page.html', vacancies = searchResult, page_numerator = pageNumeratorHTML, search_text = searchText, resumes = resumes, form = form)

  elif current_user.roleId == 2:
    company = session.scalar(sa.select(Companies).where(Companies.userId == current_user.id))

    return render_template('account_page.html', company=company)

  return render_template('account_page.html')


@account.route('/login', methods=['GET', 'POST'])
def loginPageRoute():
  if current_user.is_authenticated:
    return redirect('/')

  form = LoginForm()

  if form.validate_on_submit():
    user = db.getDBSession().scalar(sa.select(Users).where(Users.email == form.email.data))

    if user is None or not user.verify_password(form.password.data):
      error = 'Такого пользователя не существует' if user is None else 'Неверный пароль'
      flash(error)
      return redirect('/login')

    login_user(user, remember=False)

    return redirect('/')
  return render_template('login.html', form=form)


@account.route('/register', methods=['GET', 'POST'])
def registerPageRoute():
  if current_user.is_authenticated:
    return redirect('/')

  form = RegisterForm()
  session = db.getDBSession()
  if form.validate_on_submit():
    user = session.scalar(
      sa.select(Users).where(Users.email == form.email.data))

    if user:
      flash('Такой email уже существует')
      return redirect('/register')

    roleId = int(form.role_type.data)
    countryId = 183  # default - Russia
    username = form.username.data
    created = datetime.datetime.now()
    email = form.email.data
    emailVerified = 0  # default not verified
    password = form.password.data
    user = Users(roleId=roleId,
                 created=created,
                 countryId=countryId,
                 userName=username,
                 email=email,
                 emailVerified=emailVerified
                 )
    user.set_password(password)

    try:
      session.add(user)
      session.commit()
    except Exception as e:
      session.rollback()
      return f"{e}"
    return redirect('/')
  return render_template('register.html', form=form)


@account.route('/logout')
def logoutPageRoute():
  logout_user()
  return redirect('/')
