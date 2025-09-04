# Flask app factory
import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

CUSTOM_SECRET = 'change-this-to-a-random-string-1234567890'
app = Flask(__name__)
app.secret_key = CUSTOM_SECRET
CORS(app)
# Use DATABASE_URL from environment if available (for Render), else default to local
db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:1234@localhost:5432/attendance_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from app import routes
