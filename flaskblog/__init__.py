from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__,
            template_folder='Templates')  # Name of module, so flask knows where to look for templates, static files etc...
app.config['SECRET_KEY'] = 'ae9a7dc8ffe641613296f5efc0c5fa8a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

from flaskblog import routes
