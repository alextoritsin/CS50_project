import requests
import os
import urllib.parse
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

load_dotenv()


# create app instance
app = Flask(__name__)

# create db instance
db = SQLAlchemy(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stocks.db'

if not os.path.exists(os.path.join(basedir, 'stocks.db')):
    db.create_all()
    db.session.commit()


# create crypt library
bcrypt = Bcrypt(app)

# set up secret key
app.config['SECRET_KEY'] = os.getenv('CS50_SECRET_KEY')

# create login instance
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please, log in to access this page'
login_manager.login_message_category = 'info'

api_key = os.getenv('IEX_API_KEY')


def lookup(symbol):
    """Look up quote for symbol."""
    # Contact API
    try:
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"],
            "date": quote["latestUpdate"],
            "change": quote["change"]
        }
    except (KeyError, TypeError, ValueError):
        return None

from application import views