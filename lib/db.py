from flask import current_app, g
from flask_caching import Cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

cache = Cache()

def getDBEngine():
  if 'dbe' not in g:
    g.dbe = create_engine(
      current_app.config['SQLALCHEMY_DATABASE_URI'],
      echo = current_app.config['SQLALCHEMY_ECHO'],
      pool_size = current_app.config['SQLALCHEMY_POOL_SIZE'],
      max_overflow = current_app.config['SQLALCHEMY_MAX_OVERFLOW']
    )

  return g.dbe

def getDBSession():
  if 'dbs' not in g:
    g.dbs = Session(bind = getDBEngine())

  return g.dbs

def closeDBSession(e = None):
  dbs = g.pop('dbs', None)

  if dbs is not None:
      dbs.close()
