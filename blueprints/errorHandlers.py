from flask import Blueprint, render_template


errorHandlers = Blueprint('errorHandlers', __name__, template_folder = 'templates')

@errorHandlers.app_errorhandler(404)
def http404(e):
  return render_template('errors/404.html'), 404
