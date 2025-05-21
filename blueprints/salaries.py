from flask import Blueprint, render_template, request, current_app, redirect
from sqlalchemy import select, text, join, desc, asc
from flask_login import current_user

from lib import db
from lib import searchFunc

import sys, datetime, urllib, re

sys.path.append('../blocks')

from blocks import numerator


itemsPerPage = 20

salaries = Blueprint('salaries', __name__, template_folder='templates', url_prefix='/salaries')


@salaries.route('/')
def salariesPageRoute():
  session = db.getDBSession()

  pageURLArgName = 'page'
  page = int(request.args.get(pageURLArgName, 1))

  if (page < 1):
    page = 1

  limit = itemsPerPage
  offset = (page - 1) * itemsPerPage

  searchVacanciesCount = searchFunc.doSearch('topSalaryVacancies', '', '', offset, limit, '', '', True)
  searchResult = searchFunc.doSearch('topSalaryVacancies', '', '', offset, limit, '', '')

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

  pagesTotal = 5

  pageNumeratorHTML = numerator.NumeratorBlock.create({
    'currentPage': page,
    'pagesTotal': pagesTotal,
    'baseURL': paginationBaseURL,
    'pageNumberPrefix': f"?{paginationURLPrefix}"
  })

  return render_template('salaries.html', vacancies = searchResult, page_numerator = pageNumeratorHTML)
