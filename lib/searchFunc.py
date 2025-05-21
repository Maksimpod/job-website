import sys

from lib import db

from sqlalchemy import select, func, asc, desc
from sqlalchemy.sql.expression import text
from sqlalchemy.dialects.mysql import match

from datamodels import Companies, Vacancies, Resumes, Users



def doSearch(entityType: str, property: str, text: str, offset: int = 0, limit: int = 20,
  sortOrder: str = 'desc', sortBy: str = '', returnCountOnly: bool = False) -> dict|bool:

  result = False
  searchQuery = None
  sortFunc = asc if (sortOrder == 'asc') else desc

  if (text != ''):
    text = str(text).replace("'\"", '')
    property = str(property).replace("'\"", '')
    searchMatchExpr = None

    match entityType:
      case 'vacancies' | 'companyVacancies':
        match property:
          case 'title':
            searchMatchExpr = match(
              Vacancies.title,
              against = text
            ).in_natural_language_mode()
          case 'description':
            searchMatchExpr = match(
              Vacancies.description,
              against = text
            ).in_natural_language_mode()

        if (entityType == 'companyVacancies'):
          searchMatchExpr = match(
            Vacancies.title,
            against = text
          ).in_natural_language_mode()

        if (searchMatchExpr is not None):
          if (returnCountOnly):
            searchQuery = (func.count().select().select_from(Vacancies))

            if (entityType == 'companyVacancies'):
              searchQuery = searchQuery.where(Vacancies.companyId == Companies.id)
          else:
            searchQuery = (select(
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
                (Companies.employeesCount).label('companyEmployeesCount'),

                (searchMatchExpr).label('searchScore'),
                (searchMatchExpr * 10 + Vacancies.score).label('complexScore')
              )
              .where(Vacancies.companyId == Companies.id)
              .order_by(sortFunc('complexScore'))
            )

          searchQuery = searchQuery.where(searchMatchExpr)

          if (entityType == 'companyVacancies'):
            searchQuery = searchQuery.where(Companies.id == property)

      case 'resumes':
        match property:
          case 'position':
            searchMatchExpr = match(
              Resumes.position,
              against = text
            ).in_natural_language_mode()
          case 'about':
            searchMatchExpr = match(
              Resumes.about,
              against = text
            ).in_natural_language_mode()

        if (searchMatchExpr is not None):
          if (returnCountOnly):
            searchQuery = (func.count().select().select_from(Resumes))
          else:
            searchQuery = (select(
                (Resumes.id).label('resumeId'),
                (Resumes.created).label('resumeCreated'),
                (Resumes.position).label('resumePosition'),
                (Resumes.salaryFrom).label('resumeSalaryFrom'),
                (Resumes.salaryCurrencyCode).label('resumeSalaryCurrencyCode'),
                (Resumes.about).label('resumeAbout'),

                (Users.id).label('userId'),
                (Users.created).label('userCreated'),
                (Users.userName).label('userName'),
                (Users.fullName).label('userFullName'),
                (Users.gender).label('userGender'),
                (Users.birthDate).label('userBirthDate'),
                (Users.description).label('userDescription'),

                (searchMatchExpr).label('searchScore'),
                (searchMatchExpr).label('complexScore')
              )
              .where(Resumes.userId == Users.id)
              .order_by(sortFunc('complexScore'))
            )

          searchQuery = searchQuery.where(searchMatchExpr)

      case 'companies':
        match property:
          case 'title':
            searchMatchExpr = match(
              Companies.title,
              against = text
            ).in_natural_language_mode()

        if (searchMatchExpr is not None):
          if (returnCountOnly):
            searchQuery = (func.count().select().select_from(Companies))
          else:
            searchQuery = (select(
                (Companies.id).label('companyId'),
                (Companies.userId).label('companyUserId'),
                (Companies.created).label('companyCreated'),
                (Companies.title).label('companyTitle'),
                (Companies.description).label('companyDescription'),
                (Companies.website).label('companyWebsite'),
                (Companies.industry).label('companyIndustry'),
                (Companies.foundationYear).label('companyFoundationYear'),
                (Companies.employeesCount).label('companyEmployeesCount'),

                (searchMatchExpr).label('searchScore'),
                (searchMatchExpr).label('complexScore')
              )
              .order_by(sortFunc('complexScore'))
            )

          searchQuery = searchQuery.where(searchMatchExpr)

  else:
    match entityType:
      case 'topSalaryVacancies':
        searchQuery = (select(
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
            .where(Vacancies.companyId == Companies.id)
            .where(Vacancies.salaryFrom != None)
            .order_by(desc(Vacancies.salaryFrom))
          )

      case 'vacancies' | 'companyVacancies':
        searchSortBy = {
          'date': 'vacancyCreated',
          'salary': 'vacancySalaryFrom'
        }

        if (returnCountOnly):
          searchQuery = (func.count().select().select_from(Vacancies))

          if (entityType == 'companyVacancies'):
            searchQuery = searchQuery.where(Vacancies.companyId == Companies.id)
        else:
          searchQuery = (select(
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
            .where(Vacancies.companyId == Companies.id)
            .order_by(sortFunc(searchSortBy[sortBy]))
          )

        if (entityType == 'companyVacancies'):
          searchQuery = searchQuery.where(Companies.id == property)

      case 'resumes':
        searchSortBy = {
          'date': 'resumeCreated',
          'salary': 'resumeSalaryFrom'
        }

        if (returnCountOnly):
          searchQuery = (func.count().select().select_from(Resumes))
        else:
          searchQuery = (select(
              (Resumes.id).label('resumeId'),
              (Resumes.created).label('resumeCreated'),
              (Resumes.position).label('resumePosition'),
              (Resumes.salaryFrom).label('resumeSalaryFrom'),
              (Resumes.salaryCurrencyCode).label('resumeSalaryCurrencyCode'),
              (Resumes.about).label('resumeAbout'),

              (Users.id).label('userId'),
              (Users.created).label('userCreated'),
              (Users.userName).label('userName'),
              (Users.fullName).label('userFullName'),
              (Users.gender).label('userGender'),
              (Users.birthDate).label('userBirthDate'),
              (Users.description).label('userDescription')
            )
            .where(Resumes.userId == Users.id)
            .order_by(sortFunc(searchSortBy[sortBy]))
          )

      case 'companies':
        if (returnCountOnly):
          searchQuery = (func.count().select().select_from(Companies))
        else:
          searchQuery = (select(
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
            .order_by(asc(Companies.title))
          )

  ## @debug
  ## print(str(searchQuery.compile(db.getDBSession().get_bind()))) ; sys.exit(1)

  if (searchQuery is not None):
    if (not(returnCountOnly)):
      searchQuery = searchQuery.offset(offset).limit(limit)

    session = db.getDBSession()
    searchResult = session.execute(searchQuery)

    if (searchResult):
      if (returnCountOnly):
        resultsCount = 0

        for searchResultItem in searchResult:
          if (len(searchResultItem) == 1):
            resultsCount = int(searchResultItem[0])

        result = resultsCount
      else:
        result = []

        for searchResultItem in searchResult:
          match entityType:
            case 'vacancies' | 'companyVacancies' | 'topSalaryVacancies':
              result.append({
                'vacancy': {
                  'id': searchResultItem.vacancyId,
                  'created': (searchResultItem.vacancyCreated).strftime('%Y.%m.%d %H:%M:%S'),
                  'title': searchResultItem.vacancyTitle,
                  'salary': {
                    'from': (str(searchResultItem.vacancySalaryFrom) if (searchResultItem.vacancySalaryFrom is not None) else None),
                    'to': (str(searchResultItem.vacancySalaryTo) if (searchResultItem.vacancySalaryTo is not None) else None),
                    'period': searchResultItem.vacancySalaryPeriod,
                    'currency': searchResultItem.vacancySalaryCurrencyCode
                  },
                  'experience': searchResultItem.vacancyExperienceYears,
                  'description': (str(searchResultItem.vacancyDescription) if (searchResultItem.vacancyDescription is not None) else None),
                  'location': searchResultItem.vacancyLocation,
                  'locationGeo': {
                    'lat': (str(searchResultItem.vacancyLocationGeoLat) if (searchResultItem.vacancySalaryFrom is not None) else None),
                    'lng': (str(searchResultItem.vacancyLocationGeoLng) if (searchResultItem.vacancySalaryFrom is not None) else None)
                  }
                },
                'company': {
                  'id': searchResultItem.companyId,
                  'userId': searchResultItem.companyUserId,
                  'created': (searchResultItem.companyCreated).strftime('%Y.%m.%d %H:%M:%S'),
                  'title': searchResultItem.companyTitle,
                  'description': (str(searchResultItem.companyDescription) if (searchResultItem.companyDescription is not None) else None),
                  'website': searchResultItem.companyWebsite,
                  'industry': searchResultItem.companyIndustry,
                  'foundationYear': searchResultItem.companyFoundationYear,
                  'employeesCount': searchResultItem.companyEmployeesCount
                },
                ## @debug
                ## 'searchScore': round(searchResultItem.searchScore, 3),
                ## 'complexScore': round(searchResultItem.complexScore, 3)
              })

            case 'resumes':
              result.append({
                'resume': {
                  'id': searchResultItem.resumeId,
                  'created': (searchResultItem.resumeCreated).strftime('%Y.%m.%d %H:%M:%S'),
                  'position': searchResultItem.resumePosition,
                  'salary': {
                    'from': (str(searchResultItem.resumeSalaryFrom) if (searchResultItem.resumeSalaryFrom is not None) else None),
                    'currency': searchResultItem.resumeSalaryCurrencyCode
                  },
                  'about': searchResultItem.resumeAbout
                },
                'user': {
                  'id': searchResultItem.userId,
                  'created': (searchResultItem.userCreated).strftime('%Y.%m.%d %H:%M:%S'),
                  'name': searchResultItem.userName,
                  'fullName': searchResultItem.userFullName,
                  'gender': searchResultItem.userGender,
                  'birthDate': searchResultItem.userBirthDate,
                  'description': searchResultItem.userDescription
                },
                ## @debug
                ## 'searchScore': round(searchResultItem.searchScore, 3),
                ## 'complexScore': round(searchResultItem.complexScore, 3)
              })

            case 'companies':
              result.append({
                'company': {
                  'id': searchResultItem.companyId,
                  'userId': searchResultItem.companyUserId,
                  'created': (searchResultItem.companyCreated).strftime('%Y.%m.%d %H:%M:%S'),
                  'title': searchResultItem.companyTitle,
                  'description': (str(searchResultItem.companyDescription) if (searchResultItem.companyDescription is not None) else None),
                  'website': searchResultItem.companyWebsite,
                  'industry': searchResultItem.companyIndustry,
                  'foundationYear': searchResultItem.companyFoundationYear,
                  'employeesCount': searchResultItem.companyEmployeesCount
                },
                ## @debug
                ## 'searchScore': round(searchResultItem.searchScore, 3),
                ## 'complexScore': round(searchResultItem.complexScore, 3)
              })

  return result
