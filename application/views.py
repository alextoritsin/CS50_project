
import concurrent.futures as cf
import json
import pytz
from datetime import datetime

import okama as ok
import plotly
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from dateutil.relativedelta import relativedelta
from flask import (flash, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_login import current_user, login_required, login_user, logout_user

from application import app, db, lookup
from application.forms import (BuyAsset, CreateList,
                               LoginForm, PasswordChangeForm,
                               QuoteForm, RegisterForm, SearchForm, SellAsset)
from application.models import Favourites, History, Holdings, Lists, Users


@app.route("/companies", methods=["GET", "POST"])
@login_required
def companies():
    """Construct json data for US companies"""
    # query US companies
    query = ok.symbols_in_namespace('US')
    # change column names
    query = query.rename(columns={"name": "label", "ticker": "value"})
    filt = (query['type'] == 'Common Stock')
    data = query[filt].sort_values('label')
    return jsonify(data.iloc[:, [2, 1]].to_dict(orient='records'))


@app.route("/")
@app.route("/homepage", methods=["GET", "POST"])
def homepage():
    return render_template("homepage.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    form = RegisterForm()
    # check if validation is ok and user clicked on submit button
    if form.validate_on_submit():
        new_user = Users(username=form.username.data,
                         password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash(
            f'Account created for {new_user.username}. Please, log in.', 'success')
        return redirect(url_for('login'))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    # grab user data from db
    user_exist = Users.query.filter_by(username=form.username.data).first()
    if form.validate_on_submit():

        # check if the user exist and password correct
        if user_exist and user_exist.correct_password(entered_password=form.password.data):
            login_user(user_exist)
            flash(
                f'Success! You are logged in as {user_exist.username}.', category='success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash(f'Username and password do not match. Try again.',
                  category='danger')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    logout_user()
    flash('You have been logged out!', category='info')

    # Redirect user to homepage
    return redirect(url_for('homepage'))


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    form = QuoteForm()
    if form.validate_on_submit():
        symbol = form.symbol.data

        def get_info(symbol):
            return yf.Ticker(symbol).info

        def get_yearly(symbol):
            return yf.Ticker(symbol).financials

        def get_quarterly(symbol):
            return yf.Ticker(symbol).quarterly_financials
        # run concurrent queries
        with cf.ThreadPoolExecutor() as executor:
            info = executor.submit(get_info, symbol)
            year = executor.submit(get_yearly, symbol)
            quarter = executor.submit(get_quarterly, symbol)
            # iex = executor.submit(lookup, symbol)

        quote = info.result()
        session['symbol'] = quote['symbol']
        session['longName'] = quote['longName']
        prev = quote['previousClose']
        change = session['quote']['change']
        delta = round((change / prev) * 100, 2)

        # get timezone
        tz = pytz.timezone(quote['exchangeTimezoneName'])

        # get current time and last trading time
        now = datetime.now(tz).strftime("%B %#d")
        last_tday = session['quote']['date']
        last_tday = datetime.fromtimestamp(
            last_tday // 1000).strftime("%B %#d")
        day = (now == last_tday) or last_tday

        # create id's with favourite assets
        lists = Lists.query.filter_by(user_id=current_user.id).all()
        in_fav = Favourites.query.filter_by(
            user_id=current_user.id, symbol=quote['symbol']).all()
        if in_fav:
            ids = {row.list_id for row in in_fav}
        else:
            ids = {}

        # Bar chart explained at
        # https://plotly.com/python/bar-charts/#colored-and-styled-bar-chart
        def makeGraph(period, company, str_yearly):
            # select specific rows
            income = period.loc['Net Income']
            income.index = list(period.columns.strftime('%Y-%m-%d'))
            total_rev = period.loc['Total Revenue']
            total_rev.index = list(period.columns.strftime('%Y-%m-%d'))

            fig = go.Figure()
            fig.add_trace(go.Bar(x=income.index, y=income, name='Net Income',
                                 marker_color='rgb(26, 118, 255)', marker_line_width=0.1))
            fig.add_trace(go.Bar(x=income.index, y=total_rev, name='Total Revenue',
                                 marker_color='rgb(55, 83, 109)', marker_line_width=0.1))
            fig.update_layout(xaxis=dict(
                tickmode='array', tickvals=income.index))
            fig.update_layout(title=f'{company} {str_yearly} Financials', xaxis_tickfont_size=14,
                              yaxis=dict(
                                  title=quote['financialCurrency'], titlefont_size=16, tickfont_size=14),
                              legend=dict(x=0, y=1.0,
                                          bgcolor='rgba(255, 255, 255, 0)',
                                          bordercolor='rgba(255, 255, 255, 0)'
                                          ),
                              barmode='group',
                              bargap=0.15,
                              bargroupgap=0.1
                              )
            graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            return graph
        # make graphs with 2 periods
        yearly = makeGraph(year.result(), quote['longName'], 'Yearly')
        quarterly = makeGraph(quarter.result(), quote['longName'], 'Quarterly')

        return render_template('quoted.html', form=form, ids=ids, in_fav=in_fav,
                               quote=quote, delta=delta, lists=lists, change=change,
                               yearly=yearly, quarterly=quarterly, day=day)
    return render_template('quote.html', form=form)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    form = BuyAsset()
    if form.validate_on_submit():
        # calculate purchase summ
        quote = lookup(form.symbol.data)
        shares = form.shares.data
        purchase_summ = quote["price"] * shares

        # get datetime
        date = datetime.now().strftime("%x, %X")
        current_user.cash -= purchase_summ

        # # update user history
        update = History()
        update.add_operation(current_user, "Purchase",
                             quote["name"], quote["symbol"], shares, quote["price"], date)

        # update user holdings
        portfolio = Holdings.query.filter_by(
            user_id=current_user.id, symbol=quote["symbol"]).first()

        if portfolio == None:
            # when first purchase of company
            portfolio = Holdings()
            portfolio.add_asset(current_user, shares,
                                quote["name"], quote["symbol"], quote["price"])
            flash(
                f'Successfull purchase {shares} share(s) of {quote["name"]} for ${quote["price"]}.', category='success')
        else:
            # when company already in holdings
            portfolio.mean_price = (
                portfolio.mean_price * portfolio.shares + purchase_summ) / (portfolio.shares + shares)
            portfolio.shares += shares
            db.session.commit()
            flash(
                f'Successfull purchase {shares} share(s) of {quote["name"]} for ${quote["price"]}.', category='success')
        return redirect(url_for('buy'))
    return render_template("buy.html", form=form)


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    form = SellAsset()
    form.company.choices = [(row.symbol, f'{row.company} ({row.shares} pcs.)')
                            for row in Holdings.query.filter_by(user_id=current_user.id)]

    holdings = Holdings.query.filter_by(user_id=current_user.id).first()

    input_shares = form.shares.data
    company = Holdings.query.filter_by(
        user_id=current_user.id, symbol=form.company.data).first()

    if form.validate_on_submit():

        if input_shares == company.shares:
            db.session.delete(company)
        else:
            company.shares -= input_shares
        db.session.commit()

        # query user and stock price
        user = Users.query.get(current_user.id)
        quote = lookup(company.symbol)

        # update cash
        user.cash += input_shares * quote["price"]

        # update history table
        date = datetime.now().strftime("%x, %X")
        update = History()
        update.add_operation(
            current_user, "Sell", quote["name"], quote["symbol"], input_shares, quote["price"], date)
        flash(
            f'Successfully sold {input_shares} share(s) of {company.company}', category='success')
        return redirect(url_for('sell'))

    return render_template("/sell.html", form=form, holdings=holdings)


@app.get("/index")
@login_required
def index():
    '''Show portfolio of stocks'''
    # get holdings info
    holdings = Holdings.query.filter_by(user_id=current_user.id).first()

    if not holdings:
        return render_template('index.html', holdings=holdings)

    # convert sqlobject to dict, result in list of dictionaries
    cash = current_user.cash
    holdings = Holdings.query.filter_by(user_id=current_user.id).all()

    grand_total = 0
    price_on_buy = 0

    symbols = [row.symbol for row in holdings]
    # calculate future values with concurrent method
    with cf.ThreadPoolExecutor() as executor:
        quotes = executor.map(lookup, symbols)
        for index, quote in enumerate(quotes):
            holdings[index].price = quote["price"]
            holdings[index].total = quote['price'] * holdings[index].shares
            grand_total += quote["price"] * holdings[index].shares
            price_on_buy += holdings[index].mean_price * holdings[index].shares

    dif = price_on_buy - grand_total
    db.session.commit()
    return render_template('index.html', holdings=holdings, total=grand_total, cash=cash, delta=dif)


@app.get("/history")
@login_required
def history():
    """Show history of transactions"""
    operations = History.query.filter_by(user_id=current_user.id).all()
    return render_template("history.html", operations=operations)


@app.route("/password_change", methods=["GET", "POST"])
@login_required
def password_change():
    """Change password and username"""
    user = Users.query.filter_by(id=current_user.id).first()
    form = PasswordChangeForm()
    if form.validate_on_submit():
        name = form.username.data
        password = form.password.data
        if name != user.username:
            user.username = name
            if password:
                user.password = password
                db.session.commit()
                logout_user()
                flash(
                    'Successfully changed name and password. Please, log in', 'success')
                return redirect(url_for('login'))
            else:
                db.session.commit()
                flash(f'Changed name to "{name}"', 'success')
                return redirect(url_for('password_change'))
        elif password:
            user.password = password
            db.session.commit()
            logout_user()
            flash('Successfully changed password. Please, log in', 'success')
            return redirect(url_for('login'))
        else:
            return redirect(url_for('password_change'))
    return render_template('password_change.html', form=form, value=user.username)


@app.route("/lists", methods=["GET", "POST"])
@login_required
def lists():
    """Manage lists with favourite assets"""
    form = CreateList()
    lists = Lists.query.filter_by(user_id=current_user.id).all()
    if form.validate_on_submit():
        lists = Lists()
        lists.new_list(current_user, form.name.data)
        flash(f'Successfully created new list', category='success')
        return redirect(url_for('lists'))
    return render_template("lists.html", lists=lists, form=form)


@app.post("/favourites")
@login_required
def favourites():
    """Get post request with favourites list id's"""
    data = request.get_json()
    symbol = session['symbol']
    corp = session['longName']
    set_my_ids = Favourites.query.filter_by(user_id=current_user.id,
                                            symbol=symbol).all()
    if not data['data']:
        # asset have been deleted from favourites if any
        if len(set_my_ids) > 0:
            set_my_ids = {row.list_id for row in set_my_ids}
            Favourites.query.filter(Favourites.list_id.in_(set_my_ids)).\
                filter_by(symbol=symbol).delete()
    else:
        set_fav_ids = set(data['data'])
        if len(set_my_ids) == 0:
            # if no such a company in user lists, add all that in set_fav_ids
            for id in set_fav_ids:
                company = Favourites()
                company.add_tolist(current_user, id, corp, symbol)
        else:
            # already have asset in 1 or more user lists
            set_my_ids = {row.list_id for row in set_my_ids}
            # find and delete assets in user lists that is not in fav lists
            to_del = set_my_ids - set_fav_ids
            if len(to_del) > 0:
                Favourites.query.filter(Favourites.list_id.in_(to_del)).\
                    filter_by(symbol=symbol).delete()
            # add assets that is in fav lists and is not in user lists
            to_add = set_fav_ids - set_my_ids
            if len(to_add) > 0:
                for id in to_add:
                    company = Favourites()
                    company.add_tolist(current_user, id, corp, symbol)
    db.session.commit()
    return jsonify(data)


@app.route("/lists/<int:list_id>/delete", methods=["POST"])
@login_required
def delete_list(list_id):
    """Delete chosen list"""
    list = Lists.query.filter_by(user_id=current_user.id, id=list_id).first()
    for company in list.assets:
        db.session.delete(company)
    db.session.delete(list)
    db.session.commit()
    flash(f'Successfully delete list', category='success')
    return redirect(url_for('lists'))


@app.post("/lists/<int:list_id>/edit")
@login_required
def edit_list(list_id):
    """Edit list"""
    data = request.form.getlist('myCheckbox')
    name = request.form.get("change_name")
    lst = Lists.query.filter_by(id=list_id).first()
    if name != lst.name:
        lst.name = name

    if data:
        Favourites.query.filter(Favourites.symbol.in_(data)).\
            filter_by(user_id=current_user.id,
                      list_id=list_id).delete()
    db.session.commit()
    return redirect(url_for('lists'))


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search quote and compare companies performance
       with US inflation                        """
    form = SearchForm()
    now = datetime.now()
    last_year = (now + relativedelta(months=-13)).strftime("%Y-%m")
    last_two = (now + relativedelta(months=-25)).strftime("%Y-%m")
    last_five = (now + relativedelta(months=-61)).strftime("%Y-%m")

    def makeGraph(period, form_data):
        df = ok.AssetList(form_data, first_date=period).wealth_indexes
        col_names = list(df.columns)
        fig = px.line(df, x=df.index.astype(str), y=col_names,
                      labels={"x": "", "value": "Wealth index",
                              "variable": "Assets"},
                      title='Wealth indexes compared to US inflation')
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    if form.validate_on_submit():
        data = form.name.data.split(', ')[:-1]
        assets = list(map(lambda x: (x + '.US'), data))

        with cf.ThreadPoolExecutor() as executor:
            graphOne = executor.submit(makeGraph, last_year, assets)
            graphTwo = executor.submit(makeGraph, last_two, assets)
            graphFive = executor.submit(makeGraph, last_five, assets)

        return render_template('search.html', form=form, g_JSON_one=graphOne.result(),
                               g_JSON_two=graphTwo.result(), g_JSON_five=graphFive.result())

    return render_template('search.html', form=form)
