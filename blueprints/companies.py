from flask import Blueprint, render_template, request, current_app, redirect
from sqlalchemy import select, asc
from flask_login import current_user
from werkzeug.datastructures import MultiDict

from forms import CompanyMainForm

from datamodels import Users, Vacancies, Companies, Contacts, ContactTypes, t_companyContacts
from lib import db
from lib import searchFunc

import sqlalchemy as sa
import sys, datetime, urllib, re

sys.path.append('../blocks')

from blocks import numerator

itemsPerPage = 20

companies = Blueprint('companies', __name__, template_folder='templates', url_prefix='/companies')


@companies.route('/')
def companiesPageRoute():
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

  searchCompaniesCount = searchFunc.doSearch('companies', 'title', searchText, offset, limit, sortOrder, sortBy, True)
  searchResult = searchFunc.doSearch('companies', 'title', searchText, offset, limit, sortOrder, sortBy)

  for searchResultItem in searchResult:
    if (('company' in searchResultItem) and isinstance(searchResultItem['company'], dict)):
      if ('created' in searchResultItem['company']):
        searchResultItem['company']['created'] = datetime.datetime.strptime(searchResultItem['company']['created'],
                                                                            '%Y.%m.%d %H:%M:%S')
      if ('description' in searchResultItem['company']):
        searchResultItem['company']['description'] = re.sub(r"<[^>]*?>", ' ',
                                                            str(searchResultItem['company']['description']))

  requestArgs = request.args.to_dict()

  if (pageURLArgName in requestArgs):
    del requestArgs[pageURLArgName]

  requestArgs['page'] = ''

  paginationURLPrefix = urllib.parse.urlencode(requestArgs)
  paginationBaseURL = request.url_rule.rule

  if (paginationBaseURL.endswith('/')):
    paginationBaseURL = paginationBaseURL[:-1]

  pagesTotal = int(searchCompaniesCount / itemsPerPage)

  if (searchCompaniesCount % itemsPerPage > 0):
    pagesTotal += 1

  pageNumeratorHTML = numerator.NumeratorBlock.create({
    'currentPage': page,
    'pagesTotal': pagesTotal,
    'baseURL': paginationBaseURL,  ## request.url_rule.rule,
    'pageNumberPrefix': f"?{paginationURLPrefix}"
  })

  return render_template('companies.html', companies=searchResult, total_companies=searchCompaniesCount,
                         current_sort=sortBy, current_order=sortOrder, page_numerator=pageNumeratorHTML,
                         search_text=searchText)


@companies.route('/<int:companyId>')
def companyPageRoute(companyId):
  if companyId < 1:
    return redirect("404.html")

  session = db.getDBSession()

  company = session.scalar(
    sa.select(Companies).where(Companies.id == companyId)
  )

  if not company:
    return redirect("404.html")

  sortBy = request.args.get('sort', 'date')
  sortOrder = request.args.get('order', 'desc')
  searchText = request.args.get('search', '').strip()

  pageURLArgName = 'page'
  page = int(request.args.get(pageURLArgName, 1))

  if (page < 1):
    page = 1

  limit = itemsPerPage
  offset = (page - 1) * itemsPerPage

  searchVacanciesCount = searchFunc.doSearch('companyVacancies', companyId, searchText, offset, limit, sortOrder,
                                             sortBy, True)
  searchResult = searchFunc.doSearch('companyVacancies', companyId, searchText, offset, limit, sortOrder, sortBy)

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
  paginationBaseURL = f"/companies/{companyId}"

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

  query = (select(
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
           .where(Companies.id == companyId)
           .limit(1)
           )

  companyResult = {}

  result = session.execute(query)
  resultItem = result.one()

  if (resultItem):
    contacts = {}

    contactsQuery = (select(
      (Contacts.value).label('contactValue'),
      (ContactTypes.title).label('contactTypeTitle')
    )
                     .where(t_companyContacts.c.companyId == companyId)
                     .where(t_companyContacts.c.contactId == Contacts.id)
                     .where(Contacts.contactTypeId == ContactTypes.id)
                     .order_by(asc(Contacts.contactTypeId))
                     .order_by(asc(Contacts.id))
                     )

    contactsResult = session.execute(contactsQuery)

    for contactsResultItem in contactsResult:
      if (contactsResultItem.contactTypeTitle not in contacts):
        contacts[contactsResultItem.contactTypeTitle] = []

      contacts[contactsResultItem.contactTypeTitle].append(contactsResultItem.contactValue)

    companyResult = {
      'company': {
        'id': resultItem.companyId,
        'userId': resultItem.companyUserId,
        'created': datetime.datetime.strptime((resultItem.companyCreated).strftime('%Y.%m.%d %H:%M:%S'),
                                              '%Y.%m.%d %H:%M:%S'),
        'title': resultItem.companyTitle,
        'description': (str(resultItem.companyDescription) if (resultItem.companyDescription is not None) else None),
        'website': resultItem.companyWebsite,
        'industry': resultItem.companyIndustry,
        'foundationYear': resultItem.companyFoundationYear,
        'employeesCount': resultItem.companyEmployeesCount,
        'contacts': contacts
      }
    }

  return render_template('company.html', companyResult=companyResult, vacancies=searchResult,
                         total_vacancies=searchVacanciesCount,
                         current_sort=sortBy, current_order=sortOrder, page_numerator=pageNumeratorHTML,
                         search_text=searchText)


@companies.route('/create', methods=['GET', 'POST'])
def createCompanyPageRoute():
  session = db.getDBSession()
  if not current_user.is_authenticated:
    return redirect("/login")

  userId = current_user.get_id()

  user = session.scalar(
    sa.select(Users).where(Users.id == userId))

  if user.roleId != 2:
    return redirect("/")

  form = CompanyMainForm()

  if form.validate_on_submit():
    created = datetime.datetime.now()
    title = form.title.data
    description = form.description.data
    website = form.website.data
    foundationYear = form.found.data
    employeesCount = form.employees.data

    company = Companies(userId=userId,
                        created=created,
                        title=title,
                        description=description,
                        website=website,
                        foundationYear=foundationYear,
                        employeesCount=employeesCount,
                        )

    email = Contacts(
      contactTypeId=2,
      value=form.email.data
    )

    address = Contacts(
      contactTypeId=1,
      value=form.adress.data
    )

    tel = Contacts(
      contactTypeId=4,
      value=form.tel.data
    )

    try:
      session.add(company)
      session.add(email)
      session.add(address)
      session.add(tel)
      session.flush()

      session.execute(
        t_companyContacts.insert().values([
          {'companyId': company.id, 'contactId': email.id},
          {'companyId': company.id, 'contactId': address.id},
          {'companyId': company.id, 'contactId': tel.id}
        ])
      )

      session.commit()
    except Exception as e:
      session.rollback()
      return f"{e}"
    return redirect("/account_page")

  return render_template('create_company.html', form=form)


@companies.route('/edit/<int:companyId>', methods=['GET', 'POST'])
def editCompanyPageRoute(companyId):
  session = db.getDBSession()

  if not current_user.is_authenticated:
    return redirect("/login")

  company = session.scalar(
    sa.select(Companies).where(Companies.id == companyId))

  if not company or company.userId != int(current_user.get_id()):
    return redirect("404.html")

  contacts = session.scalars(select(Contacts)
                             .join(t_companyContacts, Contacts.id == t_companyContacts.c.contactId)
                             .where(t_companyContacts.c.companyId == companyId)).all()

  form = CompanyMainForm()

  if request.method == 'GET':
    if company:
      form.title.data = company.title
      form.description.data = company.description
      form.website.data = company.website
      form.found.data = company.foundationYear
      form.employees.data = company.employeesCount

    for contact in contacts:
      if contact.contactTypeId == 2:
        form.email.data = contact.value

      if contact.contactTypeId == 1:
        form.adress.data = contact.value

      if contact.contactTypeId == 4:
        form.tel.data = contact.value

  if "POST" == request.method:
    form_data = request.form.copy()

    form = CompanyMainForm(formdata=MultiDict(form_data))

    if form.validate_on_submit():
      try:
        company.title = form.title.data
        company.description = form.description.data
        company.website = form.website.data
        company.foundationYear = form.found.data
        company.employeesCount = form.employees.data

        for contact in contacts:
          if contact.contactTypeId == 2:
            contact.value = form.email.data

          if contact.contactTypeId == 1:
            contact.value = form.adress.data

          if contact.contactTypeId == 4:
            contact.value = form.tel.data

        session.commit()
      except Exception as e:
        session.rollback()
        return f"{e}"

      return redirect("/account_page")

  return render_template('edit_company.html', form=form)
