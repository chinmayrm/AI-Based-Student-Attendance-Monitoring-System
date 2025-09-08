# Flask app factory
import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

CUSTOM_SECRET = 'change-this-to-a-random-string-1234567890'
app = Flask(__name__)
app.secret_key = CUSTOM_SECRET
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
	'DATABASE_URL',
	'postgresql://studentattendence_u1rx_user:q7ayUsTp2Ul2iCqHeCy1VJetoQ1lqEJQ@dpg-d2srajumcj7s73ah3dl0-a.oregon-postgres.render.com/studentattendence_u1rx'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from app import routes
