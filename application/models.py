from sqlalchemy.orm import backref
from application import db, login_manager
from application import bcrypt
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    cash = db.Column(db.Integer(), nullable=False, default=10000)
    portfolio = db.relationship('Holdings', backref='owner', lazy=True)
    operations = db.relationship('History', backref='trader', lazy=True)   

    def __repr__(self):
        return f'User {self.username}, cash: {self.cash}'

    # @property
    # def cash_usd(self):
    #     return f'${self.cash}'

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, text_password):
        self.password_hash = bcrypt.generate_password_hash(text_password).decode('utf-8')

    def correct_password(self, entered_password):
        return bcrypt.check_password_hash(self.password_hash, entered_password)


class Holdings(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    shares = db.Column(db.Integer(), nullable=False, default=0)
    company = db.Column(db.String(length=60), nullable=False, unique=True)
    symbol = db.Column(db.String(length=10), nullable=False, unique=True)
    mean_price = db.Column(db.Float(precision=32, asdecimal=False, decimal_return_scale=None), nullable=False)
    price = db.Column(db.Float(precision=32, asdecimal=False, decimal_return_scale=None))
    total = db.Column(db.Float(precision=32, asdecimal=False, decimal_return_scale=None))
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    
    def add_asset(self, user_obj, num_of_shares, comp, sym, mean):
        self.user_id = user_obj.id
        self.shares = num_of_shares
        self.company = comp
        self.symbol = sym
        self.mean_price = mean
        db.session.add(self)
        db.session.commit()


class History(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    type = db.Column(db.String(10), nullable=False)
    company = db.Column(db.String(60), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    shares = db.Column(db.Integer(), nullable=False)
    price = db.Column(db.Float(precision=32, asdecimal=False, decimal_return_scale=None), nullable=False)
    date = db.Column(db.String(15), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)

    def add_operation(self, user_obj, type_of, comp, ticker, shares_num, price, date):
        self.user_id = user_obj.id
        self.type = type_of
        self.company = comp
        self.symbol = ticker
        self.shares = shares_num
        self.price = price
        self.date = date
        db.session.add(self)
        db.session.commit()

"""  
from application import db
from application.models import Lists, Favourites
       Drop table
Lists.__table__.drop(db.session.bind)

            Create table
Lists.__table__.create(db.session.bind)
"""
class Lists(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    assets = db.relationship('Favourites', backref='lists', lazy=True)

    def __repr__(self):
        return f'<{self.name}>'

    def new_list(self, user_obj, name):
        self.user_id = user_obj.id
        self.name = name
        db.session.add(self)
        db.session.commit()

class Favourites(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    company = db.Column(db.String(60), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    # price = db.Column(db.Float(precision=32, asdecimal=False, decimal_return_scale=None))
    list_id = db.Column(db.Integer(), db.ForeignKey('lists.id'), nullable=False)  
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<{self.symbol} in list {self.list_id}>'

    def add_tolist(self, user_obj, list_id, company, symbol):
        self.user_id = user_obj.id
        self.list_id = list_id
        self.company = company
        self.symbol = symbol
        db.session.add(self)
        # db.session.commit()
