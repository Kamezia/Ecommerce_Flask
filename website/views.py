from flask import Blueprint, redirect, session, url_for, render_template, request, flash, jsonify, make_response, current_app
from . import db
from flask_login import login_user, current_user, logout_user
from .models import User, Item
from .forms import PurchaseItemForm, SellItemForm
import app
import jwt
import datetime
from functools import wraps



views = Blueprint("views", __name__)

#THIS WAY TO ACCESS THE HOME PAGE WHEN YOU TYPING THE TOKEN IN THE URL LIKE: http://127.0.0.1:5000/home?token=yjeufruu4u4ru
# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = request.args.get('token')

#         if not token:
#             return jsonify({'message' : 'Token is missing !!'}), 401

#         try:
#             data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
#             user = User.query.filter_by(username=data['user']).first()
#         except:
#             return jsonify({'message' : 'Token is invalid !!'}), 401
#         return  f(user, *args, **kwargs)
#     return decorated



# HERE WE USE TOKEN BY PUTTING IT IN AUTHORIZATION.
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = session['token']
            # Here we decode (return normal data) by using decode function.
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"]) # --> this return the payload.
            user = User.query.filter_by(username=data['username']).first() # search on our database of such username.
        except:
            return jsonify({'message' : 'Token is invalid !!'}), 401
        return f(user, *args, **kwargs)
    return decorated


@views.route("/")
@views.route("/home")
@token_required
def home_page(user):
    return render_template("home.html", user=current_user)

@views.route("/market", methods=['POST', 'GET'])
def market_page():
    purchase_form = PurchaseItemForm()
    selling_form = SellItemForm()
    if request.method == "POST":
        # Buying item logic
        purchase_item = request.form.get('purchase_item')
        p_item_object = Item.query.filter_by(name=purchase_item).first()
        if p_item_object:
            if current_user.budget < p_item_object.price or current_user.budget<=0:
                flash(f"Sorry, your budget not enough to buy this item: {p_item_object.name}!", category='danger')
            else:

                p_item_object.owner = current_user.id
                current_user.budget-=p_item_object.price
                db.session.commit()
                flash(f"Congratulations! You have bought the {p_item_object.name} right now.", category='success')
        # Selling item logic        
        sold_item = request.form.get('sell_item')
        s_item_object = Item.query.filter_by(name=sold_item).first()
        if s_item_object:
            if s_item_object in current_user.items:
                s_item_object.owner = None
                current_user.budget += s_item_object.price
                db.session.commit()
                flash(f"Okay, you have already sold this item '{s_item_object.name}' right now.", category='success')
            else:
                flash("Somthing went wrong in selling this item")
        return redirect(url_for("views.market_page"))

    if request.method == 'GET':
        items = Item.query.filter_by(owner=None)
        owned_items = Item.query.filter_by(owner=current_user.id) # Here we show the items that the owner has.
        return render_template('market.html', selling_form=selling_form ,items=items, user=current_user, purchase_form=purchase_form, owned_items=owned_items)



@views.route("/register", methods=['POST', 'GET'])
def sign_up():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password1 = request.form['password1']
        password2 = request.form['password2']

        email_exist = User.query.filter_by(email=email).first()
        username_exist = User.query.filter_by(username=username).first()

        if email_exist:
            flash("This Email is already exists", category='danger')
        elif username_exist:
            flash("This username is already exists", category='danger')
        elif password1!=password2:
            flash("Password does not match", category='danger')
        elif len(password1) < 6:
            flash("Password length should be greater than 6", category='danger')
        elif len(email)<6:
            flash("The length of email is very short", category='danger')
        else:
            new_user = User(email=email, username=username)
            new_user.hash_password(password1) 
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash("User Created!", category='success')
            return redirect(url_for("views.home_page"))


    return render_template("register.html", user=current_user)


@views.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

       
        if  username and password: # We verify any amount of fields.
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash("Logged successfully", category='success')
                token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=90)}, current_app.config['SECRET_KEY'], algorithm='HS256') # Here we create a JWT token by hashing its components [header + payload + secret key]
                session['token'] = token
                return redirect(url_for("views.home_page"))

            else:
                flash("There is an error in Password or Username", category='danger')
           

        return make_response('Could not verify!', 401, {'WWW-authenticate': 'Basic realm ="Login Required"'})


        

    return render_template('login.html', user=current_user)


@views.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("views.sign_up"))