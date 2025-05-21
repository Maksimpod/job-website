from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound


staticPages = Blueprint('staticPages', __name__, template_folder = 'templates', url_prefix = '')

@staticPages.route('/', defaults = {'pageName': 'index'})
@staticPages.route('/<pageName>')
def staticPageRoute(pageName):
  try:
    return render_template(f'pages/{pageName}.html')
  except TemplateNotFound:
    abort(404)
