import requests
import os
import urllib.parse
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


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
app.config['SECRET_KEY'] = '610da25ac8aa58a362ab49de7d2e9c37'

# create login instance
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please, log in to access this page'
login_manager.login_message_category = 'info'

api_key = 'pk_f61364335c1b47cd9add54a5b1e12211'


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