from flask import Blueprint, render_template, request, current_app, redirect, url_for
from sqlalchemy import select, text, join, desc, asc, exists, and_
from flask_login import current_user
from werkzeug.datastructures import MultiDict

from forms import VacancyMainInfoForm
from datamodels import Users, Vacancies, Companies, VacancyResponses

from lib import db, utility
from lib import searchFunc

import sqlalchemy as sa
import sys, datetime, urllib, re

sys.path.append('../blocks')

from blocks import numerator

itemsPerPage = 20

vacancies = Blueprint('vacancies', __name__, template_folder='templates', url_prefix='/vacancies')


@vacancies.route('/')
@db.cache.cached(query_string=True)
def vacanciesPageRoute():
  session = db.getDBSession()

  sortBy = request.args.get('sort', 'date')
  sortOrder = request.args.get('order', 'desc')
  searchText = request.args.get('search', '').strip()

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
        searchResultItem['vacancy']['created'] = datetime.datetime.strptime(searchResultItem['vacancy']['created'],
                                                                            '%Y.%m.%d %H:%M:%S')
      if ('description' in searchResultItem['vacancy']):
        searchResultItem['vacancy']['description'] = re.sub(r"<[^>]*?>", ' ',
                                                            str(searchResultItem['vacancy']['description']))

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

  return render_template('vacancies.html', vacancies=searchResult, total_vacancies=searchVacanciesCount,
                         current_sort=sortBy, current_order=sortOrder, page_numerator=pageNumeratorHTML,
                         search_text=searchText)


@vacancies.route('/<int:vacancyId>')
def vacancyPageRoute(vacancyId):
  if vacancyId < 1:
    return redirect("404.html")

  session = db.getDBSession()

  vacancy = session.scalar(
    sa.select(Vacancies).where(Vacancies.id == vacancyId))

  if not vacancy:
    return redirect("404.html")

  query = (select(
    (Vacancies.id).label('vacancyId'),
    (Vacancies.created).label('vacancyCreated'),
    (Vacancies.title).label('vacancyTitle'),
    (Vacancies.salaryFrom).label('vacancySalaryFrom'),
    (Vacancies.salaryTo).label('vacancySalaryTo'),
    (Vacancies.salaryCurrencyCode).label('vacancySalaryCurrencyCode'),
    (Vacancies.salaryPeriod).label('vacancySalaryPeriod'),
    (Vacancies.experienceYears).label('vacancyExperienceYears'),
    (Vacancies.description).label('vacancyDescription'),
    (Vacancies.location).label('vacancyLocation'),
    (Vacancies.locationGeoLat).label('vacancyLocationGeoLat'),
    (Vacancies.locationGeoLng).label('vacancyLocationGeoLng'),

    (Companies.id).label('companyId'),
    (Companies.userId).label('companyUserId'),
    (Companies.created).label('companyCreated'),
    (Companies.title).label('companyTitle'),
    (Companies.description).label('companyDescription'),
    (Companies.website).label('companyWebsite'),
    (Companies.industry).label('companyIndustry'),
    (Companies.foundationYear).label('companyFoundationYear'),
    (Companies.employeesCount).label('companyEmployeesCount')
  )
           .where(Vacancies.id == vacancyId)
           .where(Vacancies.companyId == Companies.id)
           .limit(1)
           )

  vacancyResult = {}

  result = session.execute(query)
  resultItem = result.one()

  if (resultItem):
    vacancyResult = {
      'vacancy': {
        'id': resultItem.vacancyId,
        'created': datetime.datetime.strptime((resultItem.vacancyCreated).strftime('%Y.%m.%d %H:%M:%S'),
                                              '%Y.%m.%d %H:%M:%S'),
        'title': resultItem.vacancyTitle,
        'salary': {
          'from': (str(resultItem.vacancySalaryFrom) if (resultItem.vacancySalaryFrom is not None) else None),
          'to': (str(resultItem.vacancySalaryTo) if (resultItem.vacancySalaryTo is not None) else None),
          'period': resultItem.vacancySalaryPeriod,
          'currency': resultItem.vacancySalaryCurrencyCode
        },
        'experience': resultItem.vacancyExperienceYears,
        'description': (str(resultItem.vacancyDescription) if (resultItem.vacancyDescription is not None) else None),
        'location': resultItem.vacancyLocation,
        'locationGeo': {
          'lat': (str(resultItem.vacancyLocationGeoLat) if (resultItem.vacancySalaryFrom is not None) else None),
          'lng': (str(resultItem.vacancyLocationGeoLng) if (resultItem.vacancySalaryFrom is not None) else None)
        }
      },
      'company': {
        'id': resultItem.companyId,
        'userId': resultItem.companyUserId,
        'created': (resultItem.companyCreated).strftime('%Y.%m.%d %H:%M:%S'),
        'title': resultItem.companyTitle,
        'description': (str(resultItem.companyDescription) if (resultItem.companyDescription is not None) else None),
        'website': resultItem.companyWebsite,
        'industry': resultItem.companyIndustry,
        'foundationYear': resultItem.companyFoundationYear,
        'employeesCount': resultItem.companyEmployeesCount
      }
    }

  has_responded = False
  if current_user.is_authenticated:
    has_responded = session.query(
      exists().where(and_(
        VacancyResponses.vacancyId == vacancyId,
        VacancyResponses.userId == current_user.id
      ))
    ).scalar()

  return render_template('vacancy.html', vacancyResult=vacancyResult, has_responded=has_responded)


@vacancies.route('/<int:vacancyId>/response', methods=['POST'])
def vacancy_response(vacancyId):
  session = db.getDBSession()
  try:
    existing_response = session.get(VacancyResponses,
                                    {'vacancyId': vacancyId, 'userId': current_user.id})

    if existing_response:
      return redirect(url_for('vacancies.vacancyPageRoute', vacancyId=vacancyId))

    new_response = VacancyResponses(
      vacancyId=vacancyId,
      userId=current_user.id,
      created=datetime.datetime.now(),
      status=0
    )

    session.add(new_response)
    session.commit()

  except Exception as e:
    session.rollback()
    return f"{e}"

  return redirect(url_for('vacancies.vacancyPageRoute', vacancyId=vacancyId))


@vacancies.route('/create', methods=['GET', 'POST'])
def createVacancyPageRoute():
  session = db.getDBSession()
  if not current_user.is_authenticated:
    return redirect("/login")

  userId = int(current_user.get_id())

  user = session.scalar(
    sa.select(Users).where(Users.id == userId))

  if user.roleId != 2:
    return redirect("/")

  form = VacancyMainInfoForm()

  if form.validate_on_submit():
    created = datetime.datetime.now()
    salaryfrom = form.salaryfrom.data
    salaryto = form.salaryto.data
    salaryCurrencyCode = "RUR"
    exp = form.experience.data
    title = form.title.data
    desc = form.description.data
    location = form.location.data if form.location.data else None
    location = location + "; " + form.place.label.text if form.place.data else location
    location = location + "; " + form.remote.label.text if form.remote.data else location
    location = location + "; " + form.hybrid.label.text if form.hybrid.data else location
    location = location + "; " + form.moving.label.text if form.moving.data else location

    company = session.scalar(
      sa.select(Companies).where(Companies.userId == userId))

    vacancy = Vacancies(created=created,
                        companyId=company.id,
                        salaryFrom=salaryfrom,
                        salaryTo=salaryto,
                        salaryCurrencyCode=salaryCurrencyCode,
                        experienceYears=exp,
                        title=title,
                        description=desc,
                        location=location,
                        )
    try:
      session.add(vacancy)
      session.commit()
    except Exception as e:
      session.rollback()
      return f"{e}"
    return redirect("/account_page")
  return render_template('create_vacancy.html', form=form)


@vacancies.route('/edit/<int:vacancyId>', methods=['GET', 'POST'])
def editVacancyPageRoute(vacancyId):
  session = db.getDBSession()
  if not current_user.is_authenticated:
    return redirect("/login")

  userId = int(current_user.get_id())

  user = session.scalar(
    sa.select(Users).where(Users.id == userId))

  if user.roleId != 2:
    return redirect("/")

  vacancy = session.scalar(
    sa.select(Vacancies).where(Vacancies.id == vacancyId))

  company = session.scalar(
    sa.select(Companies).where(Companies.userId == userId))

  if not vacancy or vacancy.companyId != company.id:
    return redirect("404.html")

  form = VacancyMainInfoForm()

  if request.method == 'GET':
    if company:
      form.title.data = vacancy.title
      form.salaryfrom.data = int(vacancy.salaryFrom) if vacancy.salaryFrom else None
      form.salaryto.data = int(vacancy.salaryTo) if vacancy.salaryTo else None
      form.experience.data = vacancy.experienceYears if vacancy.experienceYears else None
      form.description.data = vacancy.description if vacancy.experienceYears else None
      form.location.data = vacancy.location.split(';')[0] if vacancy.location else None

      if form.place.label.text in vacancy.location:
        form.place.data = True

      if form.remote.label.text in vacancy.location:
        form.remote.data = True

      if form.hybrid.label.text in vacancy.location:
        form.hybrid.data = True

      if form.moving.label.text in vacancy.location:
        form.moving.data = True

  if "POST" == request.method:
    form_data = request.form.copy()

    form = VacancyMainInfoForm(formdata=MultiDict(form_data))

    if form.validate_on_submit():
      vacancy.salaryFrom = form.salaryfrom.data
      vacancy.salaryTo = form.salaryto.data
      vacancy.experienceYears = form.experience.data
      vacancy.title = form.title.data
      vacancy.description = form.description.data

      location = form.location.data if form.location.data else None
      location = location + "; " + form.place.label.text if form.place.data else location
      location = location + "; " + form.remote.label.text if form.remote.data else location
      location = location + "; " + form.hybrid.label.text if form.hybrid.data else location
      location = location + "; " + form.moving.label.text if form.moving.data else location

      vacancy.location = location

      try:
        session.commit()
      except Exception as e:
        session.rollback()
        return f"{e}"
      return redirect("/account_page")
  return render_template('edit_vacancy.html', form=form)


@vacancies.route('/my', methods=['GET', 'POST'])
@db.cache.cached(query_string=True)
def myVacanciesPageRoute():
  if not current_user.is_authenticated:
    return redirect("/login")

  if current_user.roleId != 2:
    return redirect("/")

  session = db.getDBSession()
  userId = int(current_user.id)

  company = session.scalar(
    sa.select(Companies).where(Companies.userId == userId)
  )

  if company:
    sortBy = request.args.get('sort', 'date')
    sortOrder = request.args.get('order', 'desc')
    searchText = request.args.get('search', '').strip()

    pageURLArgName = 'page'
    page = int(request.args.get(pageURLArgName, 1))

    if (page < 1):
      page = 1

    limit = itemsPerPage
    offset = (page - 1) * itemsPerPage

    searchVacanciesCount = searchFunc.doSearch('companyVacancies', company.id, searchText, offset, limit, sortOrder,
                                               sortBy, True)
    searchResult = searchFunc.doSearch('companyVacancies', company.id, searchText, offset, limit, sortOrder, sortBy)

    for searchResultItem in searchResult:
      if (('vacancy' in searchResultItem) and isinstance(searchResultItem['vacancy'], dict)):
        if ('created' in searchResultItem['vacancy']):
          searchResultItem['vacancy']['created'] = datetime.datetime.strptime(searchResultItem['vacancy']['created'],
                                                                              '%Y.%m.%d %H:%M:%S')
        if ('description' in searchResultItem['vacancy']):
          searchResultItem['vacancy']['description'] = re.sub(r"<[^>]*?>", ' ',
                                                              str(searchResultItem['vacancy']['description']))

    requestArgs = request.args.to_dict()

    if (pageURLArgName in requestArgs):
      del requestArgs[pageURLArgName]

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

    return render_template('my_vacancies.html', vacancies=searchResult, company=company, utility=utility,
                           page_numerator=pageNumeratorHTML)
  else:
    vacancies = []

    return render_template('my_vacancies.html', vacancies=vacancies, company=company, utility=utility)



@vacancies.route('/delete/<int:vacancyId>', methods=['POST'])
def delete_vacancy(vacancyId):
  session = db.getDBSession()
  userId = int(current_user.id)

  try:
    vacancy = session.get(Vacancies, vacancyId)
    company = session.scalar(
      sa.select(Companies).where(Companies.userId == userId)
    )

    if not vacancy or not company or vacancy.companyId != company.id:
      return redirect("404.html")

    session.execute(
      sa.delete(VacancyResponses)
      .where(VacancyResponses.vacancyId == vacancyId)
    )

    session.delete(vacancy)

    session.commit()
  except Exception as e:
    session.rollback()
    return f"{e}"

  return redirect(url_for('vacancies.myVacanciesPageRoute'))
