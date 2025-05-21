from flask import Blueprint


ctxProcessors = Blueprint('ctxProcessors', __name__, url_prefix = None)

@ctxProcessors.app_context_processor
def injectTemplateGlobals():
  import datetime

  return dict({
    'globals': {
      'currentYear': (datetime.datetime.utcnow()).year
    }
  })
