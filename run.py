from flask import Flask
from flask_login import LoginManager
from flask_caching import Cache

from lib import db

from blueprints.ctxProcessors import ctxProcessors
from blueprints.errorHandlers import errorHandlers
from blueprints.staticPages import staticPages
from blueprints.vacancies import vacancies
from blueprints.account import account
from blueprints.resume import resume
from blueprints.responses import responses
from blueprints.candidates import candidates
from blueprints.companies import companies
from blueprints.salaries import salaries
from blueprints.searchVacancies import searchVacancies
from blueprints.searchResumes import searchResumes
from blueprints.api import api

from datamodels import Users


application = Flask(__name__, static_url_path="", static_folder="static")
application.config.from_envvar('APP_CONFIG_PATH')
application.url_map.strict_slashes = False

application.teardown_appcontext(db.closeDBSession)

login = LoginManager()
login.init_app(application)

cache.init_app(application)

@login.user_loader
def loadUser(id):
  return db.getDBSession().get(Users, int(id))

application.register_blueprint(ctxProcessors)
application.register_blueprint(errorHandlers)
application.register_blueprint(vacancies)
application.register_blueprint(account)
application.register_blueprint(resume)
application.register_blueprint(responses)
application.register_blueprint(candidates)
application.register_blueprint(companies)
application.register_blueprint(salaries)
application.register_blueprint(searchVacancies)
application.register_blueprint(searchResumes)

application.register_blueprint(api)

application.register_blueprint(staticPages)


if __name__ == "__main__":
  application.run()
