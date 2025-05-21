from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, RadioField, TelField, DateField, SelectField, \
  IntegerField, TextAreaField, BooleanField, FormField, FieldList, validators, URLField
from wtforms.validators import DataRequired, Email, Length, Optional, URL


class RegisterForm(FlaskForm):
  role_type = RadioField('Вы регистрируетесь как:',
                         choices=[('3', 'Соискатель'), ('2', 'Работодатель')],
                         default='3',
                         validators=[DataRequired()])
  username = StringField('Никнейм', validators=[DataRequired(message="Укажите никнейм!")],
                         render_kw={"placeholder": "Введите никнейм"})
  email = EmailField('Почта', validators=[
    DataRequired(message="Укажите email"),
    Email(message="Некорректный email адрес")
  ], render_kw={"placeholder": "Введите email"})
  password = PasswordField('Пароль', validators=[
    DataRequired(message="Укажите пароль"),
    Length(min=6, message="Пароль должен быть не менее 6 символов")
  ], render_kw={"placeholder": "Введите пароль"})
  submit = SubmitField('Регистрация')


class LoginForm(FlaskForm):
  email = EmailField('Почта', validators=[
    DataRequired(message="Укажите email"),
    Email(message="Некорректный email адрес")
  ], render_kw={"placeholder": "Email "})
  password = PasswordField('Пароль', validators=[
    DataRequired(message="Укажите пароль"),
    Length(min=6, message="Слишком короткий пароль")
  ], render_kw={"placeholder": "Пароль"})
  submit = SubmitField('Войти')


class ResumeWorkplaceForm(FlaskForm):
  position = StringField('Должность', validators=[DataRequired(message="Укажите должность")],
                         render_kw={"placeholder": "Должность"})
  title = StringField('Название компании', validators=[DataRequired(message="Укажите название компании")],
                      render_kw={"placeholder": "Название компании"})
  desc = TextAreaField('Описание', render_kw={
    "placeholder": "Опишите обязанности, которые вы выполняли на данной должности.", "rows": 3})
  beginyear = IntegerField('Начало работы', validators=[DataRequired(message="Укажите год начала работы")],
                           render_kw={"placeholder": "Год начала работы"})
  endyear = IntegerField('Конец работы', validators=[Optional()],
                         render_kw={"placeholder": "Год окончания работы"})
  actual = BooleanField('Работаю в данный момент')


class ResumeEducationForm(FlaskForm):
  spec = StringField('Специальность', validators=[DataRequired(message="Укажите специальность")],
                     render_kw={"placeholder": "Специальность"})
  title = StringField('Название учебного заведения',
                      validators=[DataRequired(message="Укажите название учебного заведения")],
                      render_kw={"placeholder": "Название учебного заведения"})
  endyear = IntegerField('Год окончания', validators=[DataRequired(message="Укажите год окончания")],
                         render_kw={"placeholder": "Год окончания обучения"})


class ResumeAboutForm(FlaskForm):
  about = TextAreaField('Описание', render_kw={
    "placeholder": "Укажите личные качества/навыки, которые относятся к вашей профессиональной деятельности.",
    "rows": 3})


class ResumePositionForm(FlaskForm):
  pos = StringField('Желаемая должность', validators=[DataRequired(message="Укажите должность")],
                    render_kw={"placeholder": "Кем вы хотите работать?"})
  salary = IntegerField('Желаемая зарплата', render_kw={"placeholder": "Укажите желаемую зарплату (₽)"})


class ResumeMainInfoForm(FlaskForm):
  surname = StringField('Фамилия', validators=[DataRequired(message="Укажите фамилию")],
                        render_kw={"placeholder": "Фамилия"})
  name = StringField('Имя', validators=[DataRequired(message="Укажите имя")],
                     render_kw={"placeholder": "Имя"})
  patro = StringField('Отчество', render_kw={"placeholder": "Отчество (при наличии)"})
  gender = RadioField('Пол',
                      choices=[('M', 'Мужской'), ('F', 'Женский')],
                      default='M',
                      validators=[DataRequired()])
  tel = TelField("Контакты", validators=[DataRequired(message="Укажите телефон"), Length(max=12)],
                 render_kw={"placeholder": "Номер телефона"})
  city = StringField('Город', validators=[DataRequired(message="Укажите город")],
                     render_kw={"placeholder": "Город"})
  bdate = DateField('Дата рождения', validators=[DataRequired(message="Укажите дату рождения")])
  country = SelectField('Гражданство', coerce=int, validate_choice=False, default=183)

  workplaces = FieldList(FormField(ResumeWorkplaceForm), min_entries=0)
  educations = FieldList(FormField(ResumeEducationForm), min_entries=0)

  about = FormField(ResumeAboutForm)

  position = FormField(ResumePositionForm)

  submit = SubmitField('Сохранить')


class VacancyMainInfoForm(FlaskForm):
  title = StringField('Должность', validators=[DataRequired(message="Укажите должность")],
                      render_kw={"placeholder": "Название (должность)"})
  salaryfrom = IntegerField('Зарплата от', validators=[Optional()], render_kw={"placeholder": "Зарплата от (₽)"})
  salaryto = IntegerField('Зарплата до', validators=[Optional()], render_kw={"placeholder": "Зарплата до (₽)"})
  experience = IntegerField('Требуемый опыт', validators=[Optional()],
                            render_kw={"placeholder": "Требуемый опыт (лет)"})
  location = StringField('Фамилия', validators=[Optional()],
                         render_kw={"placeholder": "Местоположение работы (если есть)"})

  wformat = StringField('Формат работы', validators=[Optional()])
  place = BooleanField('На месте работодателя')
  remote = BooleanField('Удаленная работа')
  hybrid = BooleanField('Гибрид')
  moving = BooleanField('Разъездной')

  description = TextAreaField('Описание вакансии', validators=[DataRequired(message="Заполните описание")], render_kw={
    "placeholder": "Опишите должность, требования к кандидатам, обязанности, преимущества работы в компании.",
    "rows": 3})

  def validate_salaryfrom(self, field):
    if field.data and self.salaryto.data:
      if field.data > self.salaryto.data:
        raise validators.ValidationError('"От" не может быть больше "До"')

  submit = SubmitField('Сохранить')


class SearchMainForm(FlaskForm):
  search = StringField('Должность или компания', validators=[Optional()],
                       render_kw={"placeholder": "Должность или компания"})

  submit = SubmitField('Найти')

class CompanyMainForm(FlaskForm):
  title = StringField('Название компании', validators=[DataRequired(message="Введите название")],
                       render_kw={"placeholder": "Название компании"})
  description = TextAreaField('Описание компании', validators=[Optional()],
                      render_kw={"placeholder": "Описание компании", "rows": 3})
  adress = StringField('Телефон', validators=[Optional()],
                    render_kw={"placeholder": "Адрес главного офиса"})
  website = URLField('Сайт', validators=[URL(message="Некорректный URL")],
                            render_kw={"placeholder": "Сайт компании"})
  email = EmailField('Телефон', validators=[Email(message="Некорректный email адрес")],
                    render_kw={"placeholder": "Почта для связи"})
  tel = TelField('Телефон', validators=[Optional()],
                           render_kw={"placeholder": "Телефон"})
  found = IntegerField('Основание', validators=[Optional()],
                            render_kw={"placeholder": "Дата основания"})
  employees = IntegerField('Сотрудники', validators=[Optional()],
                       render_kw={"placeholder": "Количество сотрудников"})

  submit = SubmitField('Сохранить')
