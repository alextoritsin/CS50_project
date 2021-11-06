import concurrent.futures as cf

from flask import session
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (IntegerField, PasswordField, SelectField,
                     StringField, SubmitField)
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

from application import lookup
from application.models import Holdings, Users


class RegisterForm(FlaskForm):
    username = StringField(label='username', validators=[
                           Length(min=4, max=30), DataRequired()])
    password = PasswordField(label='password', validators=[
                             Length(min=6), DataRequired()])
    confirm_password = PasswordField(label='confirm_password', validators=[
                                     EqualTo('password'), DataRequired()])
    submit = SubmitField(label='Create Account')

    # the func name is specific to validate all username(s)
    def validate_username(self, user_to_check):
        user = Users.query.filter_by(username=user_to_check.data).first()
        if user:
            raise ValidationError('Username already exist!')


class LoginForm(FlaskForm):
    username = StringField(label='username', validators=[DataRequired()])
    password = PasswordField(label='password', validators=[DataRequired()])
    submit = SubmitField(label='Sing in')


class QuoteForm(FlaskForm):
    symbol = StringField(label='symbol', validators=[DataRequired()])
    submit = SubmitField('Quote')

    def validate_symbol(self, field):
        symbol = field.data.replace('-', '.')
        quote = lookup(symbol)
        session['quote'] = quote
        if not quote:
            raise ValidationError("Invalid ticker.")


class SellAsset(FlaskForm):
    company = SelectField('Select ticker', choices=[])
    shares = IntegerField('Shares')
    submit = SubmitField('Sell')

    def validate_shares(self, field):
        company = Holdings.query.filter_by(
            user_id=current_user.id, symbol=self.company.data).first()
        if field.data != None and (field.data < 1 or field.data > company.shares):
            if company.shares == 1:
                raise ValidationError(
                    "You can sell only 1 share of this stock.")
            else:
                raise ValidationError(
                    f"Number must be between 1 and {company.shares}.")


class BuyAsset(FlaskForm):
    symbol = StringField(label='Symbol', validators=[DataRequired()])
    shares = IntegerField(label='Shares')
    submit = SubmitField(label='Buy')

    def validate_shares(self, field):
        quote = lookup(self.symbol.data)
        if quote:
            max = current_user.cash // quote['price']
            if field.data != None and (field.data < 1 or field.data > max):
                raise ValidationError(
                    f"Number must be between 1 and {int(max)}.")

    def validate_symbol(self, field):
        if lookup(field.data) == None:
            raise ValidationError("Invalid ticker.")


class PasswordChangeForm(FlaskForm):
    username = StringField(label='Change Account Name',
                           validators=[DataRequired()])
    current_password = PasswordField(
        label='Change Password')
    password = PasswordField(label='password')
    confirm_password = PasswordField(label='confirm_password', validators=[
                                     EqualTo('password')])
    submit = SubmitField(label='Save changes')

    def validate_username(self, field):
        user = Users.query.filter_by(username=field.data).first()
        if user and user.id != current_user.id:
            raise ValidationError("This name is already taken")

    def validate_current_password(self, field):
        user = Users.query.get(int(current_user.id))
        if field.data and not user.correct_password(entered_password=field.data):
            raise ValidationError("Invalid password")

    def validate_password(self, field):
        if field.data:
            if len(field.data) < 6:
                raise ValidationError("Password must be at least 6 characters")
            if field.data == self.current_password.data:
                raise ValidationError("Provide new password")


class CreateList(FlaskForm):
    name = StringField(validators=[Length(min=2, max=15), DataRequired()])
    submit = SubmitField('Create')


class SearchForm(FlaskForm):
    name = StringField(label='Input comma sepateted symbols',
                       validators=[DataRequired()])
    submit = SubmitField('Search')

    def validate_name(self, field):
        submit = field.data.split(',')
        symbols = []
        for item in submit:
            if len(item) > 1:
                symbols.append(item.strip(" ").replace('-', '.'))
        with cf.ThreadPoolExecutor() as executor:
            responds = executor.map(lookup, symbols)
            for item in responds:
                if not item:
                    raise ValidationError("Invalid ticker.")
