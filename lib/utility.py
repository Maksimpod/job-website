import datetime

def format_years(years):
  if years % 10 == 1 and years % 100 != 11:
    return f"{years} год"
  elif 2 <= years % 10 <= 4 and (years % 100 < 10 or years % 100 >= 20):
    return f"{years} года"
  else:
    return f"{years} лет"


def calculate_work_years(workplaces):
  if not workplaces:
    return "0 лет"

  current_year = datetime.datetime.now().year
  total_years = 0

  for wp in workplaces:
    if not wp.beginYear:
      continue

    start_year = wp.beginYear
    end_year = wp.endYear if wp.endYear is not None else current_year

    if end_year < start_year:
      continue

    total_years += (end_year - start_year)

  if total_years == 0:
    total_years = 1
  return format_years(total_years)


def calculate_age(birth_date):
  today = datetime.datetime.now().date()
  age = today.year - birth_date.year

  if (today.month, today.day) < (birth_date.month, birth_date.day):
    age -= 1

  if age % 10 == 1 and age % 100 != 11:
    result = str(age) + " год"
  elif 2 <= age % 10 <= 4 and (age % 100 < 10 or age % 100 >= 20):
    result = str(age) + " года"
  else:
    result = str(age) + " лет"
  return result




def format_date(date_obj):
  month_names = [
    "января", "февраля", "марта",
    "апреля", "мая", "июня",
    "июля", "августа", "сентября",
    "октября", "ноября", "декабря"
  ]

  day = date_obj.day
  month = month_names[date_obj.month - 1]

  return f"{day} {month}"
