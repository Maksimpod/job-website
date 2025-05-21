from flask import Blueprint, render_template, redirect, request, url_for, jsonify
from sqlalchemy import text, join, desc, asc, select, delete
from flask_login import current_user
from werkzeug.datastructures import MultiDict

from forms import ResumeMainInfoForm
from datamodels import Users, Countries, Resumes, Educations, Workplaces, t_resumeEducations, t_resumeWorkplaces, \
  t_resumeSkills, Skills

from lib import db
from lib import searchFunc
from lib import utility

import sqlalchemy as sa
import sys, datetime, urllib, json

sys.path.append('../blocks')

from blocks import numerator


itemsPerPage = 20

resume = Blueprint('resume', __name__, template_folder='templates', url_prefix='/resumes')

SKIP_VALIDATION_ACTIONS = {
  'add-workplace': lambda form, data: form.workplaces.append_entry(),
  'add-education': lambda form, data: form.educations.append_entry(),
  'remove-workplace': lambda form, data: form.workplaces.entries.pop(int(data.get('remove-workplace', 0))),
  'remove-education': lambda form, data: form.educations.entries.pop(int(data.get('remove-education', 0)))
}


@resume.route('/')
def resumesPageRoute():
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

  searchResumesCount = searchFunc.doSearch('resumes', 'position', searchText, offset, limit, sortOrder, sortBy, True)
  searchResult = searchFunc.doSearch('resumes', 'position', searchText, offset, limit, sortOrder, sortBy)

  for searchResultItem in searchResult:
    searchResultItem['user']['age'] = None
    searchResultItem['user']['workYears'] = None
    searchResultItem['user']['lastWorkplace'] = None

    if (('resume' in searchResultItem) and isinstance(searchResultItem['resume'], dict)):
      if ('created' in searchResultItem['resume']):
        searchResultItem['resume']['created'] = utility.format_date(datetime.datetime.strptime(searchResultItem['resume']['created'], '%Y.%m.%d %H:%M:%S'))

    if (('user' in searchResultItem) and isinstance(searchResultItem['user'], dict)):
      if ('birthDate' in searchResultItem['user']):
        searchResultItem['user']['age'] = utility.calculate_age(searchResultItem['user']['birthDate'])

    workplaces = session.query(Workplaces) \
      .join(t_resumeWorkplaces, Workplaces.id == t_resumeWorkplaces.c.workplaceId) \
      .filter(t_resumeWorkplaces.c.resumeId == searchResultItem['resume']['id']) \
      .order_by(
        Workplaces.endYear.is_(None).desc(),    # Текущие работы (endYear=None) first
        Workplaces.endYear.desc(),              # Затем по убыванию года окончания
        Workplaces.beginYear.desc()             # Если годы одинаковые - по дате начала
    ).all()

    searchResultItem['user']['workYears'] = utility.calculate_work_years(workplaces)

    if (len(workplaces) > 0):
      searchResultItem['user']['lastWorkplace'] = {
        'title': workplaces[0].title,
        'specialisation': workplaces[0].specialisation
      }

  requestArgs = request.args.to_dict()

  if (pageURLArgName in requestArgs):
    del requestArgs[pageURLArgName]

  requestArgs['page'] = ''

  paginationURLPrefix = urllib.parse.urlencode(requestArgs)
  paginationBaseURL = request.url_rule.rule

  if (paginationBaseURL.endswith('/')):
    paginationBaseURL = paginationBaseURL[:-1]

  pagesTotal = int(searchResumesCount / itemsPerPage)

  if (searchResumesCount % itemsPerPage > 0):
    pagesTotal += 1

  pageNumeratorHTML = numerator.NumeratorBlock.create({
    'currentPage': page,
    'pagesTotal': pagesTotal,
    'baseURL': paginationBaseURL,
    'pageNumberPrefix': f"?{paginationURLPrefix}"
  })

  return render_template('resumes.html', resumes = searchResult, total_resumes = searchResumesCount,
    current_sort = sortBy, current_order = sortOrder, page_numerator = pageNumeratorHTML, search_text = searchText)


@resume.route('/create', methods=['GET', 'POST'])
def createResumePageRoute():
  session = db.getDBSession()
  if not current_user.is_authenticated:
    return redirect("/login")

  userId = current_user.get_id()

  user = session.scalar(
    sa.select(Users).where(Users.id == userId))

  if user.roleId != 3:
    return redirect("/")

  resume = session.scalar(
    sa.select(Resumes).where(Resumes.userId == user.id))

  if resume:
    redirect(url_for('resumes.myResumePageRoute'))

  form_data = request.form or {}

  form = ResumeMainInfoForm()

  for action, handler in SKIP_VALIDATION_ACTIONS.items():
    if action in form_data:
      handler(form, form_data)
      break

  countries = session.query(Countries).all()

  form.country.choices = [(country.id, country.title) for country in countries]
  form.country.default = 183

  if not any(action in form_data for action in SKIP_VALIDATION_ACTIONS):
    if form.validate_on_submit():
      name_parts = [form.name.data, form.surname.data]
      if form.patro.data:
        name_parts.append(form.patro.data)

      fullname = " ".join(name_parts)

      user.fullName = fullname
      user.gender = form.gender.data
      user.telephone = form.tel.data
      user.city = form.city.data
      user.birthDate = form.bdate.data
      user.countryId = form.country.data
      try:
        session.commit()
      except Exception as e:
        session.rollback()
        return f"{e}"

      last_id = session.execute(
        sa.select(Resumes.id).order_by(Resumes.id.desc()).limit(1)
      ).scalar() + 1
      created = datetime.datetime.now()
      salary = form.position.salary.data
      salaryCurrencyCode = "RUR"
      position = form.position.pos.data
      about = form.about.about.data
      resume = Resumes(id=last_id,
                       userId=current_user.get_id(),
                       created=created,
                       salaryFrom=salary,
                       position=position,
                       salaryCurrencyCode=salaryCurrencyCode,
                       about=about
                       )
      try:
        session.add(resume)
        session.commit()
      except Exception as e:
        session.rollback()
        return f"{e}"

      if form.workplaces.entries:
        for i, workplace in enumerate(form.workplaces.entries):
          title = workplace.title.data
          spec = workplace.position.data
          desc = workplace.desc.data
          beginyear = workplace.beginyear.data
          endyear = None if workplace.actual.data else workplace.endyear.data

          wplace = Workplaces(title=title,
                              specialisation=spec,
                              description=desc,
                              beginYear=beginyear,
                              endYear=endyear
                              )

          try:
            session.add(wplace)
            session.commit()

            new_assoc = t_resumeWorkplaces.insert().values(
              resumeId=resume.id,
              workplaceId=wplace.id
            )
            session.execute(new_assoc)
            session.commit()
          except Exception as e:
            session.rollback()
            return f"{e}"

      if form.educations.entries:
        for i, education in enumerate(form.educations.entries):
          title = education.title.data
          spec = education.spec.data
          endyear = education.endyear.data

          edu = Educations(title=title,
                           specialisation=spec,
                           endYear=endyear
                           )

          try:
            session.add(edu)
            session.commit()

            new_assoc = t_resumeEducations.insert().values(
              resumeId=resume.id,
              educationId=edu.id
            )
            session.execute(new_assoc)
            session.commit()
          except Exception as e:
            session.rollback()
            return f"{e}"

      skills_str = request.form.get('skills', '')
      skills_list = [s.strip() for s in skills_str.split(',') if s.strip()]
      if len(skills_list) > 0:
        for i, title in enumerate(skills_list):
          try:
            skill = session.execute(
              sa.select(Skills).where(Skills.title == title)
            ).scalar_one_or_none()

            if not skill:
              skill = Skills(title=title)
              session.add(skill)
              session.flush()

            session.execute(
              t_resumeSkills.insert().values(
                resumeId=resume.id,
                skillId=skill.id
              )
            )

            session.commit()
          except Exception as e:
            session.rollback()
            return f"{e}"

      return redirect("/account_page")

  return render_template('create_resume.html', form=form)


@resume.route('/edit/<int:resumeId>', methods=['GET', 'POST'])
def editResumePageRoute(resumeId):
  session = db.getDBSession()

  if not current_user.is_authenticated:
    return redirect("/login")

  resume = session.scalar(
    sa.select(Resumes).where(Resumes.id == resumeId))

  if not resume or resume.userId != int(current_user.get_id()):
    return redirect("404.html")

  user = session.scalar(
    sa.select(Users).where(Users.id == resume.userId)
  )

  countries = session.query(Countries).all()

  form = ResumeMainInfoForm()

  workplaces = session.query(Workplaces) \
    .join(t_resumeWorkplaces, Workplaces.id == t_resumeWorkplaces.c.workplaceId) \
    .filter(t_resumeWorkplaces.c.resumeId == resumeId) \
    .all()

  educations = session.query(Educations) \
    .join(t_resumeEducations, Educations.id == t_resumeEducations.c.educationId) \
    .filter(t_resumeEducations.c.resumeId == resumeId) \
    .all()

  skills = session.query(Skills) \
    .join(t_resumeSkills, Skills.id == t_resumeSkills.c.skillId) \
    .filter(t_resumeSkills.c.resumeId == resumeId) \
    .all()

  if request.method == 'GET':
    if user:
      form.name.data = user.fullName.split()[0] if user.fullName else ''
      form.surname.data = user.fullName.split()[1] if user.fullName and len(user.fullName.split()) > 1 else ''
      form.patro.data = user.fullName.split()[2] if user.fullName and len(user.fullName.split()) > 2 else ''
      form.gender.data = user.gender
      form.tel.data = user.telephone
      form.city.data = user.city
      form.bdate.data = user.birthDate
      form.country.data = user.countryId

    form.about.about.data = resume.about
    form.position.pos.data = resume.position
    form.position.salary.data = int(resume.salaryFrom)

    for i, workplace in enumerate(workplaces):
      if i >= len(form.workplaces.entries):
        form.workplaces.append_entry()
      form.workplaces.entries[i].title.data = workplace.title
      form.workplaces.entries[i].position.data = workplace.specialisation
      form.workplaces.entries[i].desc.data = workplace.description
      form.workplaces.entries[i].beginyear.data = workplace.beginYear
      form.workplaces.entries[i].endyear.data = workplace.endYear
      form.workplaces.entries[i].actual.data = workplace.endYear is None

    for i, education in enumerate(educations):
      if i >= len(form.educations.entries):
        form.educations.append_entry()
      form.educations.entries[i].title.data = education.title
      form.educations.entries[i].spec.data = education.specialisation
      form.educations.entries[i].endyear.data = education.endYear

    skill_titles = [skill.title for skill in skills]

    form.country.choices = [(c.id, c.title) for c in countries]
    form.country.data = user.countryId

  if "POST" == request.method:
    form_data = request.form.copy()

    if 'workplaces' in form_data:
      form_data['workplaces'] = json.loads(form_data['workplaces'])
    if 'educations' in form_data:
      form_data['educations'] = json.loads(form_data['educations'])

    form = ResumeMainInfoForm(formdata=MultiDict(form_data))

    for action, handler in SKIP_VALIDATION_ACTIONS.items():
      if action in form_data:
        handler(form, form_data)
        break

    form.country.choices = [(c.id, c.title) for c in countries]

    skills_str = request.form.get('skills', '')
    skill_titles = [s.strip() for s in skills_str.split(',') if s.strip()]

    if not any(action in form_data for action in SKIP_VALIDATION_ACTIONS):
      if form.validate_on_submit():
        try:
          name_parts = [form.name.data, form.surname.data]
          if form.patro.data:
            name_parts.append(form.patro.data)

          user.fullName = " ".join(name_parts)
          user.gender = form.gender.data
          user.telephone = form.tel.data
          user.city = form.city.data
          user.birthDate = form.bdate.data
          user.countryId = form.country.data

          resume.position = form.position.pos.data
          resume.salaryFrom = form.position.salary.data
          resume.about = form.about.about.data

          existing_workplace_ids = [w.id for w in workplaces]
          for i, workplace_entry in enumerate(form.workplaces.entries):
            if i < len(workplaces):
              workplace = workplaces[i]
              workplace.title = workplace_entry.title.data
              workplace.specialisation = workplace_entry.position.data
              workplace.description = workplace_entry.desc.data
              workplace.beginYear = workplace_entry.beginyear.data
              workplace.endYear = None if workplace_entry.actual.data else workplace_entry.endyear.data
            else:
              workplace = Workplaces(
                title=workplace_entry.title.data,
                specialisation=workplace_entry.position.data,
                description=workplace_entry.desc.data,
                beginYear=workplace_entry.beginyear.data,
                endYear=None if workplace_entry.actual.data else workplace_entry.endyear.data
              )
              session.add(workplace)
              session.flush()
              session.execute(
                t_resumeWorkplaces.insert().values(
                  resumeId=resume.id,
                  workplaceId=workplace.id
                )
              )

          for workplace in workplaces:
            if workplace.id not in existing_workplace_ids[:len(form.workplaces.entries)]:
              session.execute(
                t_resumeWorkplaces.delete().where(
                  t_resumeWorkplaces.c.resumeId == resume.id,
                  t_resumeWorkplaces.c.workplaceId == workplace.id
                )
              )
              session.delete(workplace)

          existing_edu_ids = [e.id for e in educations]
          for i, edu_entry in enumerate(form.educations.entries):
            if i < len(educations):
              education = educations[i]
              education.title = edu_entry.title.data
              education.specialisation = edu_entry.spec.data
              education.endYear = edu_entry.endyear.data
            else:
              education = Educations(
                title=edu_entry.title.data,
                specialisation=edu_entry.spec.data,
                endYear=edu_entry.endyear.data
              )
              session.add(education)
              session.flush()
              session.execute(
                t_resumeEducations.insert().values(
                  resumeId=resume.id,
                  educationId=education.id
                )
              )

          for education in educations:
            if education.id not in existing_edu_ids[:len(form.educations.entries)]:
              session.execute(
                t_resumeEducations.delete().where(
                  t_resumeEducations.c.resumeId == resume.id,
                  t_resumeEducations.c.educationId == education.id
                )
              )
              session.delete(education)

          skills_str = request.form.get('skills', '')
          skills_list = [s.strip() for s in skills_str.split(',') if s.strip()]
          existing_skills_dict = {s.title: s for s in skills}

          for skill_title in skills_list:
            if skill_title in existing_skills_dict:
              continue

            skill = session.query(Skills) \
              .filter(Skills.title == skill_title) \
              .first()

            if not skill:
              skill = Skills(title=skill_title)
              session.add(skill)
              session.flush()

            session.execute(
              t_resumeSkills.insert().values(
                resumeId=resume.id,
                skillId=skill.id
              )
            )

          for skill in skills:
            if skill.title not in skills_list:
              session.execute(
                t_resumeSkills.delete().where(
                  t_resumeSkills.c.resumeId == resume.id,
                  t_resumeSkills.c.skillId == skill.id
                )
              )

          session.commit()
        except Exception as e:
          session.rollback()
          return f"{e}"

        return redirect("/account_page")


  return render_template('edit_resume.html', form=form, skills_json=json.dumps(skill_titles))

@resume.route('/<int:resumeId>')
def resumePageRoute(resumeId):
  session = db.getDBSession()
  resume = session.scalar(
    sa.select(Resumes).where(Resumes.id == resumeId))

  if not resume:
    return redirect("404.html")

  user = session.scalar(
    sa.select(Users).where(Users.id == resume.userId))

  bdate = utility.calculate_age(user.birthDate) if user.birthDate else None

  country = session.scalar(
    sa.select(Countries).where(Countries.id == user.countryId)).title

  workplaces = session.execute(
    sa.select(Workplaces)
    .join(t_resumeWorkplaces, Workplaces.id == t_resumeWorkplaces.c.workplaceId)
    .where(t_resumeWorkplaces.c.resumeId == resumeId)
    .order_by(Workplaces.beginYear.desc())
  ).scalars().all()

  work_years = utility.calculate_work_years(workplaces) if workplaces else None

  educations = session.execute(
    sa.select(Educations)
    .join(t_resumeEducations, Educations.id == t_resumeEducations.c.educationId)
    .where(t_resumeEducations.c.resumeId == resumeId)
    .order_by(Educations.endYear.desc())
  ).scalars().all()

  skills = session.query(Skills) \
    .join(t_resumeSkills, Skills.id == t_resumeSkills.c.skillId) \
    .filter(t_resumeSkills.c.resumeId == resumeId) \
    .all()

  return render_template('resume.html', resume=resume, user=user, bdate=bdate, country=country, workplaces=workplaces,
                         years=work_years, educations=educations, skills=skills)


@resume.route('/my')
def myResumePageRoute():
  if not current_user.is_authenticated:
    return redirect("/login")

  if current_user.roleId != 3:
    return redirect("/")

  session = db.getDBSession()
  resumes = session.scalars(
       select(Resumes).where(Resumes.userId == current_user.id)
   ).all()

  return render_template('my_resumes.html', resumes=resumes, utility=utility)


@resume.route('/delete/<int:resumeId>', methods=['POST'])
def delete_resume(resumeId):
  session = db.getDBSession()
  resume = session.get(Resumes, resumeId)

  if not resume or resume.userId != current_user.id:
    return redirect("/")

  try:
    session.execute(
      t_resumeWorkplaces.delete().where(
        t_resumeWorkplaces.c.resumeId == resume.id
      )
    )

    session.execute(
      t_resumeEducations.delete().where(
        t_resumeEducations.c.resumeId == resume.id
      )
    )

    session.execute(
      t_resumeSkills.delete().where(
        t_resumeSkills.c.resumeId == resume.id
      )
    )

    session.delete(resume)
    session.commit()
  except Exception as e:
    session.rollback()
    return f"{e}"

  return redirect(url_for('resume.myResumePageRoute'))

@resume.route('/toggle-contacts', methods=['POST'])
def toggle_contacts():
  if not current_user.is_authenticated:
    return jsonify({'redirect': url_for('login')}), 403

  session = db.getDBSession()
  resume_id = request.form.get('resume_id')
  resume = session.scalar(sa.select(Resumes).where(Resumes.id == resume_id))
  user = session.scalar(sa.select(Users).where(Users.id == resume.userId))

  return jsonify({
    'telephone': user.telephone,
    'email': user.email
  })
