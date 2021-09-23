import okama as ok
from application import app
from flask import render_template, request, flash, redirect, url_for, session, jsonify
from application import db, lookup
from application.models import Favourites, Holdings, Users, History, Lists
from flask_login import login_required, login_user, logout_user, current_user
from application.forms import AddFavouriteForm, BuyAsset, RegisterForm, LoginForm, \
QuoteForm, BuyAsset, SellAsset, PasswordChangeForm, CreateList, SearchForm
from datetime import datetime


@app.route("/")
@app.route("/homepage", methods=["GET", "POST"])
def homepage():
    return render_template("homepage.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # if current_user.is_authenticated:
    #     return redirect(url_for('index'))
    form = RegisterForm()
    # check if validation is ok and user clicked on submit button        
    if form.validate_on_submit():            
        new_user = Users(username=form.username.data,
                        password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash(f'Account created. Logged in as {new_user.username}.', category='success')
        return redirect(url_for('homepage'))
    logout_user()
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))    
    form = LoginForm()
    if form.validate_on_submit():
        # grab user data from db
        user_exist = Users.query.filter_by(username=form.username.data).first()

        #check if the user exist and password correct
        if user_exist and user_exist.correct_password(entered_password=form.password.data):
            login_user(user_exist)
            next_page = request.args.get('next')
            flash(f'Success! You are logged in as {user_exist.username}.', category='success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash(f'Username and password do not match. Try again.', category='danger')
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
    add_form = AddFavouriteForm()
    lists = Lists.query.filter_by(user_id=current_user.id).first()
    add_form.list_name.choices = [(row.id, row.name) for row in Lists.query.filter_by(user_id=current_user.id)]
    if form.validate_on_submit():
        symbol = form.symbol.data
        qt = lookup(symbol)
        session["company"] = qt       
        if qt == None:
            flash('Invalid symbol', category='danger')
        return render_template('quote.html', qt=qt, form=form, add_form=add_form, lists=lists)

    if add_form.validate_on_submit():
        list_id = add_form.list_name.data
        company = Favourites.query.filter_by(company=session['company']['name'], list_id=list_id).first()
        if company:
            flash('Company already in list', 'info')
            return redirect(url_for('quote'))
        company = Favourites()
        company.add_tolist(current_user, list_id, session['company']['name'], 
                           session['company']['symbol'])
        flash('Successfully added to list', 'success')
        return redirect(url_for('quote'))
   
    return render_template('quote.html', qt=False, form=form, add_form=add_form, lists=lists)

     
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
        update.add_operation(current_user, "Purchase", quote["name"], quote["symbol"], shares, quote["price"], date)
        
        # update user holdings
        portfolio = Holdings.query.filter_by(user_id=current_user.id, symbol=quote["symbol"]).first()

        if portfolio == None:
            # when first purchase of company
            portfolio = Holdings()
            portfolio.add_asset(current_user, shares, quote["name"], quote["symbol"], quote["price"])                
            flash(f'Successfull purchase {shares} share(s) of {quote["name"]} for ${quote["price"]}.', category='success')
        else:
            # when company already in holdings
            portfolio.mean_price = (portfolio.mean_price * portfolio.shares + purchase_summ) / (portfolio.shares + shares)
            portfolio.shares += shares                    
            db.session.commit()
            flash(f'Successfull purchase {shares} share(s) of {quote["name"]} for ${quote["price"]}.', category='success')
        return redirect(url_for('buy'))
    return render_template("buy.html", form=form)           


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    form = SellAsset()
    form.company.choices = [(row.symbol, f'{row.company} ({row.shares} pcs.)') for row in Holdings.query.filter_by(user_id=current_user.id)]
    
    holdings = Holdings.query.filter_by(user_id=current_user.id).first()

    input_shares = form.shares.data        
    company = Holdings.query.filter_by(user_id=current_user.id, symbol=form.company.data).first()

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
        update.add_operation(current_user, "Sell", quote["name"], quote["symbol"], input_shares, quote["price"], date) 
        flash(f'Successfully sold {input_shares} share(s) of {company.company}', category='success')
        return redirect(url_for('sell'))
        
    return render_template("/sell.html", form=form, check=True, holdings=holdings)


@app.route("/index")
@login_required
def index():
    '''Show portfolio of stocks''' 
    # get holdings info
    holdings = Holdings.query.filter_by(user_id=current_user.id).first()
    
    if not holdings:
        return render_template('index.html', holdings=holdings)         
                
    grand_total = 0
    price_on_buy = 0
    # convert sqlobject to dict, result in list of dictionaries
    cash = current_user.cash
    holdings = Holdings.query.filter_by(user_id=current_user.id)
    for row in holdings:
        quote = lookup(row.symbol)
        row.price = quote["price"]
        row.total = quote["price"] * row.shares
        grand_total += row.total
        price_on_buy += row.mean_price * row.shares
    dif = price_on_buy - grand_total
    db.session.commit()  
    return render_template('index.html', holdings=holdings, total=grand_total, cash=cash, delta=dif)  
    

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    operations = History.query.all()
    length = len(operations)
    return render_template("history.html", operations=operations, length=length)


@app.route("/password_change", methods=["GET", "POST"])
@login_required
def password_change():
    """Change password"""
    form = PasswordChangeForm()
    if request.method == "POST":
        pswd = form.current_password.data
        user = Users.query.filter_by(id=current_user.id).first()
        check = user.correct_password(entered_password=pswd)
        #check if the user exist and password correct
        if not user or not check:
            return render_template('password_change.html', check=False, form=form)

        # check if validation is ok and user clicked on submit button        
        if form.validate_on_submit():
            user.password = form.password.data
            db.session.commit()
            logout_user()
            flash(f'Password has been changed. Please, log in.', category='success')
            return redirect(url_for('login'))
        return render_template('password_change.html', form=form, check=check)
    else:
        return render_template("password_change.html", form=form, check=True)

    
@app.route("/lists", methods=["GET", "POST"])
@login_required
def lists():
    """Manage lists with favourite assets"""
    form = CreateList()
    lists = Lists.query.filter_by(user_id=current_user.id).first()
    favourites = Lists.query.filter_by(user_id=current_user.id)
    if form.validate_on_submit():
        lists = Lists()
        lists.new_list(current_user, form.name.data)
        flash(f'Successfully created new list', category='success')
        return redirect(url_for('lists'))
    return render_template("lists.html", lists=lists, favourites=favourites, form=form)


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


@app.route("/lists/<int:list_id>/edit", methods=["POST"])
@login_required
def edit_list(list_id):
    """Edit list"""
    if request.method == "POST":
        data = request.form.getlist('myCheckbox')
        Favourites.query.filter(Favourites.symbol.in_(data)).delete()
        db.session.commit()
        return redirect(url_for('lists'))


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search quote."""
    form = SearchForm()
    # ls = ok.search(' ')
    return render_template('search.html', form=form)

@app.route("/companies", methods=["GET", "POST"])
@login_required
def companies():
    """get json data"""
    
    ls = ok.search('ford motor')
    return jsonify(ls)