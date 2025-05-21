from typing import List, Optional

from sqlalchemy import CheckConstraint, Column, DECIMAL, Date, DateTime, ForeignKeyConstraint, Index, Table, text
from sqlalchemy.dialects.mysql import BIGINT, CHAR, INTEGER, SMALLINT, TEXT, TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

from flask_login import UserMixin
import hashlib

Base = declarative_base()
metadata = Base.metadata


class ContactTypes(Base):
    __tablename__ = 'contactTypes'
    __table_args__ = (
        Index('title', 'title', unique=True),
    )

    id = mapped_column(SMALLINT, primary_key=True)
    title = mapped_column(VARCHAR(32), nullable=False, server_default=text("''"))
    description = mapped_column(VARCHAR(255))

    contacts: Mapped[List['Contacts']] = relationship('Contacts', uselist=True, back_populates='contactTypes')


class Countries(Base):
    __tablename__ = 'countries'
    __table_args__ = (
        Index('name', 'title_en'),
    )

    id = mapped_column(SMALLINT, primary_key=True)
    title = mapped_column(VARCHAR(255))
    title_en = mapped_column(VARCHAR(255))

    currencies: Mapped['Currencies'] = relationship('Currencies', secondary='currencyCountries',
                                                    back_populates='countries')
    users: Mapped[List['Users']] = relationship('Users', uselist=True, back_populates='countries')


class Currencies(Base):
    __tablename__ = 'currencies'
    __table_args__ = (
        CheckConstraint('(cast(`code` as char charset binary) = upper(`code`))', name='currencies_forceUppercaseCode'),
        Index('title', 'title')
    )

    code = mapped_column(CHAR(3), primary_key=True)
    symbol = mapped_column(CHAR(1), nullable=False, server_default=text("''"))
    title = mapped_column(CHAR(64))
    title_en = mapped_column(CHAR(64))

    countries: Mapped['Countries'] = relationship('Countries', secondary='currencyCountries',
                                                  back_populates='currencies')
    resumes: Mapped[List['Resumes']] = relationship('Resumes', uselist=True, back_populates='currencies')
    vacancies: Mapped[List['Vacancies']] = relationship('Vacancies', uselist=True, back_populates='currencies')


class Educations(Base):
    __tablename__ = 'educations'
    __table_args__ = (
        Index('endYear', 'endYear'),
        Index('specialisation', 'specialisation'),
        Index('title', 'title')
    )

    id = mapped_column(BIGINT, primary_key=True)
    title = mapped_column(VARCHAR(256), nullable=False)
    specialisation = mapped_column(VARCHAR(256), nullable=False)
    endYear = mapped_column(SMALLINT, nullable=False)

    resumes: Mapped['Resumes'] = relationship('Resumes', secondary='resumeEducations', back_populates='educations')


class Roles(Base):
    __tablename__ = 'roles'
    __table_args__ = (
        Index('title', 'title', unique=True),
    )

    id = mapped_column(SMALLINT, primary_key=True)
    title = mapped_column(VARCHAR(32), nullable=False, server_default=text("''"))
    title_en = mapped_column(VARCHAR(32), nullable=False, server_default=text("''"))
    description = mapped_column(VARCHAR(255))

    users: Mapped[List['Users']] = relationship('Users', uselist=True, back_populates='roles')


class Skills(Base):
    __tablename__ = 'skills'
    __table_args__ = (
        Index('status', 'status'),
        Index('title', 'title', unique=True)
    )

    id = mapped_column(BIGINT, primary_key=True)
    title = mapped_column(VARCHAR(64), nullable=False)
    status = mapped_column(SMALLINT, server_default=text("'0'"))

    resumes: Mapped['Resumes'] = relationship('Resumes', secondary='resumeSkills', back_populates='skills')


class Workplaces(Base):
    __tablename__ = 'workplaces'
    __table_args__ = (
        Index('beginYear', 'beginYear'),
        Index('endYear', 'endYear'),
        Index('specialisation', 'specialisation'),
        Index('title', 'title')
    )

    id = mapped_column(BIGINT, primary_key=True)
    title = mapped_column(VARCHAR(256), nullable=False)
    specialisation = mapped_column(VARCHAR(512), nullable=False)
    beginYear = mapped_column(SMALLINT, nullable=False)
    description = mapped_column(TEXT)
    endYear = mapped_column(SMALLINT)

    resumes: Mapped['Resumes'] = relationship('Resumes', secondary='resumeWorkplaces', back_populates='workplaces')


class Contacts(Base):
    __tablename__ = 'contacts'
    __table_args__ = (
        ForeignKeyConstraint(['contactTypeId'], ['contactTypes.id'], name='contacts_contactTypeId_fk'),
        Index('contactTypeId', 'contactTypeId')
    )

    id = mapped_column(BIGINT, primary_key=True)
    contactTypeId = mapped_column(SMALLINT, nullable=False)
    value = mapped_column(VARCHAR(255), nullable=False, server_default=text("''"))

    contactTypes: Mapped['ContactTypes'] = relationship('ContactTypes', back_populates='contacts')
    companies: Mapped['Companies'] = relationship('Companies', secondary='companyContacts', back_populates='contacts')


t_currencyCountries = Table(
    'currencyCountries', metadata,
    Column('currencyCode', CHAR(3), primary_key=True, nullable=False),
    Column('countryId', SMALLINT, primary_key=True, nullable=False),
    ForeignKeyConstraint(['countryId'], ['countries.id'], name='currencyCountries_countryId_fk'),
    ForeignKeyConstraint(['currencyCode'], ['currencies.code'], name='currencyCountries_currencyCode_fk'),
    Index('currencyCountries_countryId_fk', 'countryId')
)


class Users(UserMixin, Base):
    __tablename__ = 'users'
    __table_args__ = (
        ForeignKeyConstraint(['countryId'], ['countries.id'], name='users_countryId_fk'),
        ForeignKeyConstraint(['roleId'], ['roles.id'], name='users_roleId_fk'),
        Index('birthDate', 'birthDate'),
        Index('city', 'city'),
        Index('countryId', 'countryId'),
        Index('created', 'created'),
        Index('email', 'email', unique=True),
        Index('fullName', 'fullName'),
        Index('gender', 'gender'),
        Index('roleId', 'roleId'),
        Index('userName', 'userName')
    )

    id = mapped_column(BIGINT, primary_key=True)
    roleId = mapped_column(SMALLINT, nullable=False)
    countryId = mapped_column(SMALLINT, nullable=False)
    created = mapped_column(DateTime, nullable=False)
    userName = mapped_column(VARCHAR(32), nullable=False, server_default=text("''"))
    fullName = mapped_column(VARCHAR(64), nullable=False, server_default=text("''"))
    emailVerified = mapped_column(TINYINT, nullable=False, server_default=text("'0'"),
                                  comment='0 - unverified, 1 - verified')
    passwordHash = mapped_column(CHAR(32), nullable=False, server_default=text("''"))
    description = mapped_column(VARCHAR(255))
    website = mapped_column(VARCHAR(512))
    telephone = mapped_column(VARCHAR(32))
    email = mapped_column(VARCHAR(255))
    emailVerificationHash = mapped_column(CHAR(32))
    city = mapped_column(VARCHAR(255))
    gender = mapped_column(CHAR(1), comment='"M" - male, "F" - female')
    birthDate = mapped_column(Date)
    language = mapped_column(VARCHAR(255))
    passwordLastChange = mapped_column(DateTime)
    loginHash = mapped_column(CHAR(32))
    loginHashValidUntil = mapped_column(DateTime)
    lastLoggedIn = mapped_column(DateTime)
    lastSeen = mapped_column(DateTime)

    countries: Mapped['Countries'] = relationship('Countries', back_populates='users')
    roles: Mapped['Roles'] = relationship('Roles', back_populates='users')
    companies: Mapped[List['Companies']] = relationship('Companies', uselist=True, back_populates='users')
    resumes: Mapped[List['Resumes']] = relationship('Resumes', uselist=True, back_populates='users')
    vacancyResponses: Mapped[List['VacancyResponses']] = relationship('VacancyResponses', uselist=True,
                                                                      back_populates='users')

    def set_password(self, password):
        self.passwordHash = hashlib.md5(password.encode()).hexdigest()

    def verify_password(self, password):
        input_hash = hashlib.md5(password.encode()).hexdigest()
        return input_hash == self.passwordHash


class Companies(Base):
    __tablename__ = 'companies'
    __table_args__ = (
        ForeignKeyConstraint(['userId'], ['users.id'], name='companies_userId_fk'),
        Index('created', 'created'),
        Index('title', 'title'),
        Index('userId', 'userId')
    )

    id = mapped_column(BIGINT, primary_key=True)
    userId = mapped_column(BIGINT, nullable=False)
    created = mapped_column(DateTime, nullable=False)
    title = mapped_column(VARCHAR(64), nullable=False)
    description = mapped_column(VARCHAR(255))
    website = mapped_column(VARCHAR(512))
    industry = mapped_column(VARCHAR(64))
    foundationYear = mapped_column(SMALLINT)
    employeesCount = mapped_column(INTEGER)

    users: Mapped['Users'] = relationship('Users', back_populates='companies')
    contacts: Mapped['Contacts'] = relationship('Contacts', secondary='companyContacts', back_populates='companies')
    vacancies: Mapped[List['Vacancies']] = relationship('Vacancies', uselist=True, back_populates='companies')


class Resumes(Base):
    __tablename__ = 'resumes'
    __table_args__ = (
        ForeignKeyConstraint(['salaryCurrencyCode'], ['currencies.code'], name='resumes_salaryCurrencyCode_fk'),
        ForeignKeyConstraint(['userId'], ['users.id'], name='resumes_userId_fk'),
        Index('created', 'created'),
        Index('salaryCurrencyCode', 'salaryCurrencyCode'),
        Index('salaryFrom', 'salaryFrom'),
        Index('status', 'status'),
        Index('userId', 'userId')
    )

    id = mapped_column(BIGINT, primary_key=True)
    userId = mapped_column(BIGINT, nullable=False)
    created = mapped_column(DateTime, nullable=False)
    status = mapped_column(SMALLINT, nullable=False, server_default=text("'0'"))
    position = mapped_column(VARCHAR(128), nullable=False)
    salaryFrom = mapped_column(DECIMAL(11, 2))
    salaryCurrencyCode = mapped_column(CHAR(3))
    photoURL = mapped_column(VARCHAR(512))
    about = mapped_column(TEXT)

    educations: Mapped['Educations'] = relationship('Educations', secondary='resumeEducations',
                                                    back_populates='resumes')
    currencies: Mapped[Optional['Currencies']] = relationship('Currencies', back_populates='resumes')
    users: Mapped['Users'] = relationship('Users', back_populates='resumes')
    skills: Mapped['Skills'] = relationship('Skills', secondary='resumeSkills', back_populates='resumes')
    workplaces: Mapped['Workplaces'] = relationship('Workplaces', secondary='resumeWorkplaces',
                                                    back_populates='resumes')


t_companyContacts = Table(
    'companyContacts', metadata,
    Column('companyId', BIGINT, primary_key=True, nullable=False),
    Column('contactId', BIGINT, primary_key=True, nullable=False),
    ForeignKeyConstraint(['companyId'], ['companies.id'], name='companyContacts_companyId_fk'),
    ForeignKeyConstraint(['contactId'], ['contacts.id'], name='companyContacts_contactId_fk'),
    Index('companyContacts_contactId_fk', 'contactId')
)

t_resumeEducations = Table(
    'resumeEducations', metadata,
    Column('resumeId', BIGINT, primary_key=True, nullable=False),
    Column('educationId', BIGINT, primary_key=True, nullable=False),
    ForeignKeyConstraint(['educationId'], ['educations.id'], name='resumeEducations_educationId_fk'),
    ForeignKeyConstraint(['resumeId'], ['resumes.id'], name='resumeEducations_resumeId_fk'),
    Index('resumeEducations_educationId_fk', 'educationId')
)

t_resumeSkills = Table(
    'resumeSkills', metadata,
    Column('resumeId', BIGINT, primary_key=True, nullable=False),
    Column('skillId', BIGINT, primary_key=True, nullable=False),
    ForeignKeyConstraint(['resumeId'], ['resumes.id'], name='resumeSkills_resumeId_fk'),
    ForeignKeyConstraint(['skillId'], ['skills.id'], ondelete='RESTRICT', onupdate='RESTRICT',
                         name='resumeSkills_skillId_fk'),
    Index('resumeSkills_skillId_fk_idx', 'skillId')
)

t_resumeWorkplaces = Table(
    'resumeWorkplaces', metadata,
    Column('resumeId', BIGINT, primary_key=True, nullable=False),
    Column('workplaceId', BIGINT, primary_key=True, nullable=False),
    ForeignKeyConstraint(['resumeId'], ['resumes.id'], name='resumeWorkplaces_resumeId_fk'),
    ForeignKeyConstraint(['workplaceId'], ['workplaces.id'], name='resumeWorkplaces_workplaceId_fk'),
    Index('resumeWorkplaces_workplaceId_fk', 'workplaceId')
)


class Vacancies(Base):
    __tablename__ = 'vacancies'
    __table_args__ = (
        ForeignKeyConstraint(['companyId'], ['companies.id'], name='vacancies_companyId_fk'),
        ForeignKeyConstraint(['salaryCurrencyCode'], ['currencies.code'], name='vacancies_salaryCurrencyCode_fk'),
        Index('companyId', 'companyId'),
        Index('created', 'created'),
        Index('experienceYears', 'experienceYears'),
        Index('location', 'location'),
        Index('locationGeoLat', 'locationGeoLat'),
        Index('locationGeoLng', 'locationGeoLng'),
        Index('salaryCurrencyCode', 'salaryCurrencyCode'),
        Index('salaryFrom', 'salaryFrom'),
        Index('salaryPeriod', 'salaryPeriod'),
        Index('salaryTo', 'salaryTo'),
        Index('status', 'status'),
        Index('title', 'title')
    )

    id = mapped_column(BIGINT, primary_key=True)
    companyId = mapped_column(BIGINT, nullable=False)
    created = mapped_column(DateTime, nullable=False)
    status = mapped_column(SMALLINT, nullable=False, server_default=text("'0'"))
    title = mapped_column(VARCHAR(64), nullable=False, server_default=text("''"))
    salaryFrom = mapped_column(DECIMAL(11, 2))
    salaryTo = mapped_column(DECIMAL(11, 2))
    salaryCurrencyCode = mapped_column(CHAR(3))
    experienceYears = mapped_column(SMALLINT)
    description = mapped_column(TEXT)
    salaryPeriod = mapped_column(VARCHAR(16))
    location = mapped_column(VARCHAR(64))
    locationGeoLat = mapped_column(DECIMAL(11, 8))
    locationGeoLng = mapped_column(DECIMAL(11, 8))
    score = mapped_column(DECIMAL(5, 2))

    companies: Mapped['Companies'] = relationship('Companies', back_populates='vacancies')
    currencies: Mapped[Optional['Currencies']] = relationship('Currencies', back_populates='vacancies')
    vacancyResponses: Mapped[List['VacancyResponses']] = relationship('VacancyResponses', uselist=True,
                                                                      back_populates='vacancies')


class VacancyResponses(Base):
    __tablename__ = 'vacancyResponses'
    __table_args__ = (
        ForeignKeyConstraint(['userId'], ['users.id'], name='vacancyResponses_userId_fk'),
        ForeignKeyConstraint(['vacancyId'], ['vacancies.id'], name='vacancyResponses_vacancyId_fk'),
        Index('created', 'created'),
        Index('status', 'status'),
        Index('vacancyResponses_userId_fk', 'userId')
    )

    vacancyId = mapped_column(BIGINT, primary_key=True, nullable=False)
    userId = mapped_column(BIGINT, primary_key=True, nullable=False)
    created = mapped_column(DateTime, nullable=False)
    status = mapped_column(SMALLINT, nullable=False, server_default=text("'0'"))
    response = mapped_column(TEXT)

    users: Mapped['Users'] = relationship('Users', back_populates='vacancyResponses')
    vacancies: Mapped['Vacancies'] = relationship('Vacancies', back_populates='vacancyResponses')
