import os
import pytz
from flask import Flask, redirect, url_for,session
from flask import render_template
from flask import request

from flask_security.utils import verify_and_update_password
from flask_security import Security, current_user, SQLAlchemySessionUserDatastore, UserMixin, RoleMixin
from flask_security import login_required, roles_accepted, login_user,  hash_password, LoginForm

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column , Integer , String, ForeignKey

from flask_restful import Resource,Api
from flask_cors import CORS

from datetime import datetime




#app setup
app = Flask(__name__, template_folder="Templates")
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(current_dir,"Login.db")
api = Api(app)
CORS(app)

db = SQLAlchemy(app)
# db.init_app(app)
app.app_context().push()




#configurations

app.config['SECRET_KEY'] = 'super-secret'
app.config['SECURITY_PASSWORD_SALT'] = 'another-super-secret'
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_UNAUTHORISED_VIEW'] = None
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['WTF_CSRF_ENABLED'] = False
app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'login.html'
app.config['UPLOAD_FOLDER'] = 'static'
app.config['SECURITY_REGISTERABLE'] = True
app.app_context().push()



# Define models

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.user_id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer,autoincrement = True, primary_key=True)
    full_name = db.Column(db.String())
    email = db.Column(db.String(), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_users,backref=db.backref('users', lazy='dynamic'))
    fs_uniquifier = db.Column(db.String, unique=True, nullable=False)

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class Catagory(db.Model):
    __tablename__ = 'catagory'
    catagory_id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String())

class Product(db.Model):
    __tablename__ = 'product'
    product_id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    expiry_date = db.Column(db.String())
    price = db.Column(db.Integer())
    unit = db.Column(db.Integer())
    catagory_id = db.Column(db.Integer(),ForeignKey("catagory.catagory_id"))
    image_name = db.Column(db.String())
    description = db.Column(db.String())
    quantity = db.Column(db.Integer())

class Cart(db.Model):
    __tablename__ = 'cart'
    cart_id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(),ForeignKey ("user.user_id"))
    product_id = db.Column(db.Integer(),ForeignKey ("product.product_id"))
    quantity = db.Column(db.Integer())
    price = db.Column(db.Integer())


class Order(db.Model):
    __tablename__ = 'order'
    order_id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(),ForeignKey ("user.user_id"))
    total = db.Column(db.Integer())
    order_date =  db.Column(db.DateTime, default=datetime.utcnow)
    delivery_date = db.Column(db.Numeric())
    status = db.Column(db.String())
    receiver = db.Column(db.String(50))
    address = db.Column(db.String())
    city = db.Column(db.String())
    state = db.Column(db.String())
    pin_code = db.Column(db.Integer())
    
class Order_Details(db.Model):
    __tablename__ = 'order_details'
    order_details_id = db.Column(db.Integer(), primary_key=True)
    order_id = db.Column(db.Integer(), ForeignKey ("order.order_id"))
    product_id = db.Column(db.Integer(),ForeignKey ("product.product_id"))
    product_name = db.Column(db.String(), ForeignKey ("product.name"))
    quantity = db.Column(db.Integer())
    per_unit_price = db.Column(db.Integer())
    price = db.Column(db.Integer())


db.create_all()
app.app_context().push()

user_datastore = SQLAlchemySessionUserDatastore(db.session, User,Role)
security=Security(app, user_datastore)


#Controllers

@app.route('/login', methods = ["GET","POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')

@app.route('/custom_login', methods = ["GET","POST"])
def custom_login():
    if request.method == "POST":
        email= request.form["email"]
        password= request.form["password"]
        user=User.query.filter_by(email=email).first()
        if user:
            if verify_and_update_password(password, user):
                login_user(user)
                session['user_id'] = current_user.user_id
                return redirect(url_for("home_page"))
            else:
                return ({'error':'Incorrect Password'}), 400
        else:
            return ({'error':'Incorrect Email'}), 400

@app.route('/signup', methods=['GET', 'POST'])
def custom_signup():
    
    if request.method == "GET":
        return render_template('signup.html')
    
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")
        c_password = request.form.get("confirm_password")
        check=User.query.filter_by(email=email).first()
        if check:
            return ({'error':'email you entered already belongs to an account. Try another email.'}), 400
        else:
            if password == c_password :
                user_datastore.create_user(email=email,full_name=full_name,password=hash_password(password))
                db.session.commit()
            if password != c_password:
                return ({'error':'Password and Confirm password are not same'}), 400
        return redirect(url_for("login")) 

#####################

@app.route('/', methods = ["GET","POST"])
@login_required
def home_page():
    if request.method == "GET" :
        display_product = Product.query.all()        
        return render_template('Home_Page.html', display_product = display_product)
    
@app.route('/product', methods = ["GET","POST"])
@login_required
def product():
    if request.method == "GET":
        product_id=request.args.get('product_id')
        display_item = Product.query.filter_by(product_id=product_id).first()      
        display_item_catagory = Catagory.query.filter_by(catagory_id = display_item.catagory_id).first()
        return render_template('product.html', display_item = display_item, display_item_catagory=display_item_catagory )    
    
@app.route('/user_category', methods = ["GET","POST"])
@login_required
def user_category():
    if request.method == "GET" :
        display_catagory = Catagory.query.all()
        return render_template('user_category.html', display_catagory=display_catagory )
    
@app.route('/product_by_category_user', methods = ["GET","POST"])
@login_required
def product_by_category_user():
    if request.method == "POST" :
        category_id=request.form.get('category_id')
        display_item=Product.query.filter_by(catagory_id=category_id).all()
        name=Catagory.query.get(category_id)
        return render_template('product_by_category_user.html', display_item=display_item, name=name )

    
@app.route('/cart', methods = ["GET","POST"])
@login_required
def cart():
    if request.method == "GET" :
        user_id=current_user.user_id
        display_cart = Cart.query.join(Product).with_entities(Cart.cart_id, Cart.price, Cart.product_id, Cart.quantity, Product.name, Product.image_name).filter_by(user_id=user_id)
        total=0
        for i in display_cart:
            total=total+i.price
        return render_template('cart.html', display_cart=display_cart, total=total)

@app.route('/add_to_cart', methods = ["GET","POST"])
@login_required
def add_to_cart():
    if request.method == "POST" :
        product_id=request.form["product_id"]        
        user_id = current_user.user_id
        quantity=request.form["quantity"]
        p=request.form["price"]
        price=int(quantity)*int(p)

        cart=Cart(product_id=product_id, price=price, user_id=user_id, quantity=quantity)
        db.session.add(cart)
        db.session.commit()
        return redirect(url_for("home_page"))

@app.route('/update_cart_quantity', methods = ["GET","POST"])
@login_required
def update_cart_quantity():
    if request.method == "POST" :
        quantity=request.form["quantity"]
        cart_id=request.form["cart_id"]
        product_id = request.form["product_id"]

        product = Product.query.get(product_id)
        p=product.price
        price=int(quantity)*int(p)

        cart = Cart.query.get(cart_id)
        cart.quantity = quantity
        cart.price = price
        db.session.commit()
        return redirect(url_for("cart"))

@app.route('/order_details', methods = ["GET","POST"])
@login_required
def order_details():
    if request.method == "POST" :
        user_id=current_user.user_id
        quantity=request.form.get('quantity')
        total=request.form.get('total')
        t = int(total)
        if t == 0 :
            return {"Error" : "Can't Place empty order"}
        else:
            display_cart = Cart.query.join(Product).with_entities(Cart.cart_id, Cart.price, Cart.product_id, Cart.quantity, Product.name, Product.image_name).filter_by(user_id=user_id)
            return render_template('order_details.html', display_cart=display_cart, total=total)



@app.route('/buy', methods = ["GET","POST"])
@login_required
def buy():
    if request.method == "POST" :
        message=""
        m = ""
        user_id=current_user.user_id
        receiver=request.form['receiver']
        address=request.form['address']
        city=request.form['city']
        state=request.form['state']
        pin_code=request.form['pin_code']

        product=request.form.getlist('product')
        product_name=request.form.getlist('product_name')
        quantity=request.form.getlist('quantity')
        price=request.form.getlist('price')
        total=request.form.get('total')
        samay = pytz.timezone('Asia/Kolkata')
        order_date = datetime.now(samay)
        status = "To be updated soon"

        if not product :
            return {"Error" : "Can't Place empty order"}
        #add into order table
        length=len(product)
        if length == 1:
            prod=int(product[0])
            name=(product_name[0])
            quan = int(quantity[0])
            p=Product.query.filter_by(product_id=prod).first()
            if p.quantity>=quan:
                order=Order(user_id=user_id, order_date=order_date, receiver=receiver, address=address, city=city, state=state, pin_code=pin_code, status = status)
                db.session.add(order)
                db.session.commit()
            else:
                message=name+" "+"is out of Stock"
                return render_template("1.html", message=message)
        else:
            order=Order(user_id=user_id, order_date=order_date, receiver=receiver, address=address, city=city, state=state, pin_code=pin_code, status = status)
            db.session.add(order)
            db.session.commit()
        #Get generated order_id
        order_id=order.order_id

        length=len(product)
        for i in range(length):
            prod=int(product[i])
            name=(product_name[i])
            quan=int(quantity[i])
            pr=int(price[i])
            
            calculate_total = 0
            p=Product.query.filter_by(product_id=prod).first()
            if p.quantity>=quan:
                order=Order_Details(product_id=prod, quantity=quan, price=pr, order_id=order_id, product_name=name)
                p.quantity=p.quantity-(int(quan))                    
                db.session.add(order)
                db.session.commit()
                m = m + ", " + name
                calculate_total = calculate_total + pr
            else:
                message=message+ " " +name
                
        p = Order.query.filter_by(order_id = order_id).first()
        p.total = calculate_total
        db.session.commit()
        
        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()
            
        return render_template("1.html", message=message, m=m)

@app.route('/personal_details', methods = ["GET","POST"])
@login_required
def details_page():
    if request.method == "GET" :
        return render_template('personal_details.html')
    
@app.route('/personal_details_form', methods = ["GET","POST"])
@login_required
def personal_details():
    if request.method == "GET" :
        return render_template('personal_details_form.html')
    elif request.method == "POST" :
        return render_template('personal_details.html')
    
    
   
@app.route('/order', methods = ["GET","POST"])
@login_required
def order():
    if request.method == "GET" :
        user_id=current_user.user_id
        
        display_order = Order.query.filter_by(user_id = user_id).all()
        return render_template('order.html', display_order = display_order)

@app.route('/view_order', methods = ["GET","POST"])
@login_required
def view_order():
    if request.method == "POST" :
        user_id=current_user.user_id
        o=request.form["order_id"]
        view_order = Order_Details.query.join(Product, Order_Details.product_id == Product.product_id).with_entities(Order_Details.order_id, Order_Details.product_id, Order_Details.product_name, Order_Details.quantity, Order_Details.per_unit_price, Order_Details.price, Product.image_name).filter_by(order_id = o).all()
        
        return render_template('view_order_user.html', view_order = view_order)

@app.route('/delete_order', methods = ["GET", "POST"])
@login_required
def delete_order():
    if request.method == "GET" :
        order_id=request.args["order_id"]
        return render_template('confirm_delete_order_user.html', order_id=order_id)
    
    if request.method == "POST" :
        order_id=request.form["order_id"]
        t=Order.query.get(order_id)
        total = t.total*0.9
        #delete order details from order_details table
        Order_Details.query.filter_by(order_id=order_id).delete()
        db.session.commit()

        #delete order from order table
        delete_order= Order.query.get(order_id)
        db.session.delete(delete_order)
        db.session.commit()
        return render_template('response_of_delete_order.html', total=total)

@app.route('/confirm_delete_cart', methods = ["GET","POST"])
@login_required
def confirm_delete_cart():
    if request.method == "POST" :
        cart_id=request.form["cart_id"]
        return render_template('confirm_delete_cart.html', cart_id = cart_id)
    

@app.route('/delete_cart', methods = ["GET","POST"])
@login_required
def delete_cart():
    if request.method == "POST" :
        cart_id=request.form["cart_id"]

        cart = Cart.query.get(cart_id)
        db.session.delete(cart)
        db.session.commit()
        #return'Item removed Successfully'
        return redirect(url_for('cart'))

@app.route('/search_product', methods=["GET","POST"])
@login_required
def search_product():
    if request.method == "POST" :
        q=request.form.get('query')
        price = request.form.get('price')
        query='%'+q+'%'
        if not price:
            result=Product.query.filter(Product.name.like(query)).all()
        if price :
            result=Product.query.filter(Product.name.like(query), Product.price <= price ).all()
        return render_template('search_product.html', display_product=result, p = price, q = q)


@app.route('/search_category', methods=["GET","POST"])
@login_required
def search_category():
    if request.method == "POST" :
        q=request.form.get('query')
        query='%'+q+'%'
        result=Catagory.query.filter(Catagory.name.like(query)).all()
        return render_template('search_category.html', display_catagory=result)



####################################################################################################################
#admin controllers
    
@app.route('/admin', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def admin_home_page():
    if request.method == "GET" :
        display_product = Product.query.all()        
        return render_template('Admin_Home_Page.html', display_product = display_product)
    
@app.route('/out_of_stock_products', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def out_of_stock_products():
    if request.method == "GET" :
        display_product = Product.query.filter_by(quantity=0).all()        
        return render_template('out_of_stock.html', display_product = display_product)

@app.route('/view', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def view():
    if request.method == "POST" :
        product_id=request.form["product_id"]
        display_item = Product.query.filter_by(product_id=product_id).first()    
        display_item_catagory = Catagory.query.filter_by(catagory_id = display_item.catagory_id).first()
        return render_template('view_product.html', display_item = display_item, display_item_catagory=display_item_catagory)
    
@app.route('/add_product_form', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def add_product_form():
    if request.method == "GET" :
        category=Catagory.query.all()      
        return render_template('add_product.html', category=category)
    
@app.route('/add_product', methods = ["POST"])
@login_required
@roles_accepted('Admin')
def add_product():

    image=request.files["image"]
    image.save(os.path.join("static", image.filename))

    name=request.form["name"]
    expiry_date=request.form["expiry_date"]
    price=request.form["price"]
    unit=request.form["unit"]
    catagory_id=request.form["category_id"]
    description=request.form["description"]
    quantity=request.form["quantity"]

    current_date = datetime.now()
    expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d')
    if expiry_date < current_date:
        return {"Error":"Invalid Expiry date"}, 400
    else :
        product = Product(name=name, expiry_date=expiry_date, price=price, unit=unit, catagory_id=catagory_id, image_name=image.filename, description=description, quantity=quantity)
        db.session.add(product)
        db.session.commit()   
        return redirect(url_for('admin_home_page'))

@app.route('/edit_product_form', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def edit_product_form():
    if request.method == "POST" :
        product_id = request.form["product_id"]
        product=Product.query.filter_by(product_id = product_id).first()
        category=Catagory.query.all()
        return render_template('edit_product.html', product=product, category=category)

@app.route('/edit_product', methods = ["POST"])
@login_required
@roles_accepted('Admin')
def edit_product():

    image=request.files["image"]
    if (image):
        image.save(os.path.join('static', image.filename))
        image_name=image.filename
        t.image_name=image_name
    
    product_id=request.form["product_id"]
    name=request.form["name"]
    expiry_date=request.form["expiry_date"]
    price=request.form["price"]
    unit=request.form["unit"]
    catagory_id=request.form["category_id"]
    description=request.form["description"]
    quantity=request.form["quantity"]

    t=Product.query.filter_by(product_id=product_id).first()

    t.name=name
    t.expiry_date=expiry_date
    t.price=price
    t.unit=unit
    t.catagory_id=catagory_id
    t.description=description
    t.quantity=quantity
    

    db.session.commit()   
    return redirect(url_for('admin_home_page'))  

@app.route('/delete_product_confirmation', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def delete_product_confirmation():
    if request.method == "POST" :

        product_id=request.form["product_id"]
        return render_template('confirmation_delete_product.html', product_id=product_id)

@app.route('/delete_product', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def delete_product():
    if request.method == "POST" :

        product_id=request.form["product_id"]
        product = Product.query.filter_by(product_id=product_id).first()
        q = Order_Details.query.filter_by(product_id=product_id).first()
        print(q)
        if q :
            return {"Error":"You can't delete product. As there are orders connected with it."}
        db.session.delete(product)
        db.session.commit()    
        return redirect(url_for('admin_home_page'))
   
@app.route('/admin_category', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def admin_category():
    if request.method == "GET" :
        display_catagory = Catagory.query.all()        
        return render_template('Category.html', display_catagory = display_catagory)
    
@app.route('/product_by_category', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def product_by_category():
    if request.method == "POST" :
        category_id=request.form.get('category_id')
        categoryname=Catagory.query.get(category_id)
        display_item=Product.query.filter_by(catagory_id=category_id).all()     
        return render_template('product_by_category.html', category_id=category_id, display_item=display_item, i=categoryname)
    
@app.route('/add_category_form', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def add_category_form():
    if request.method == "GET" :                    
        return render_template('add_catagory.html')
        
@app.route('/add_category', methods = ["POST"])
@login_required
@roles_accepted('Admin')
def add_catagory():
    name=request.form["name"]
    description=request.form["description"]
   

    catagory_name = Catagory.query.filter_by(name=name).count()
    if catagory_name == 0 :
        catagory = Catagory(name=name, description=description)
        db.session.add(catagory)
        db.session.commit() 
    else:
        return "There is already a Catagory by same name"  
    return redirect(url_for('admin_category'))

@app.route('/edit_category', methods = ["GET", "POST"])
@login_required
@roles_accepted('Admin')
def edit_category():
    if request.method == "GET":
        category_id=request.args["category_id"]
        Category = Catagory.query.filter_by(catagory_id = category_id).first()
        return render_template('edit_category.html', Category = Category)
    
    if request.method == "POST":

        #Get information from html page
        category_id = request.form.get('id')
        name = request.form.get('name')
        description = request.form.get('description')

        #Get Category
        c = Catagory.query.filter_by(catagory_id = category_id).first()

        #update Information
        c.name = name
        c.description = description

        db.session.commit()

        return redirect(url_for('admin_category'))

@app.route('/confirm_delete_category', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def confirm_delete_category():
    if request.method == "POST" :
        category_id=request.form.get('category_id')
        return render_template('confirmation_delete_category.html', category_id = category_id)
 
@app.route('/delete_category', methods = ["POST"])
@login_required
@roles_accepted('Admin')
def delete_category():
    if request.method == "POST" :
        category_id=request.form.get('category_id')

    p =Product.query.filter_by(catagory_id=category_id).first()
    if p :
        return {"Error": "Can't Delete Category. As there are product in this category"}
    # db.session.commit()
    category = Catagory.query.get(category_id)
    db.session.delete(category)
    db.session.commit()

    return redirect(url_for('admin_category'))

@app.route('/search_product_admin', methods=["GET","POST"])
@login_required
@roles_accepted('Admin')
def search_product_admin():
    if request.method == "POST" :
        q=request.form.get('query')
        price = request.form.get('price')
        query='%'+q+'%'
        if not price:
            result=Product.query.filter(Product.name.like(query)).all()
        if price :
            result=Product.query.filter(Product.name.like(query), Product.price <= price ).all()

        return render_template('search_product_admin.html', display_product=result)

@app.route('/search_category_admin', methods=["GET","POST"])
@login_required
@roles_accepted('Admin')
def search_category_admin():
    if request.method == "POST" :
        q=request.form.get('query')
        query='%'+q+'%'
        result=Catagory.query.filter(Catagory.name.like(query)).all()
        return render_template('search_category_admin.html', display_catagory=result)

@app.route('/all_orders', methods=["GET","POST"])
@login_required
@roles_accepted('Admin')
def all_orders():
    if request.method == "GET" :
        result=Order.query.order_by(Order.order_date.desc()).all()
        return render_template('all_orders.html', orders=result)

@app.route('/view_order_admin', methods = ["GET","POST"])
@login_required
def view_order_admin():
    if request.method == "POST" :
        user_id=current_user.user_id
        o=request.form["order_id"]
        view_order = Order_Details.query.join(Product, Order_Details.product_id == Product.product_id).with_entities(Order_Details.order_id, Order_Details.product_id, Order_Details.product_name, Order_Details.quantity, Order_Details.per_unit_price, Order_Details.price, Product.image_name).filter_by(order_id = o).all()
        
        return render_template('view_order.html', view_order = view_order)
    
@app.route('/search_order', methods=["GET","POST"])
@login_required
@roles_accepted('Admin')
def search_order():
    if request.method == "POST" :
        q=request.form.get('query')
        query='%'+q+'%'
        result=Order.query.filter(Order.order_id.like(query)).all()
        return render_template('search_order.html', orders=result)

@app.route('/update_status', methods=["GET","POST"])
@login_required
@roles_accepted('Admin')
def update_status():
    if request.method == "POST" :
        id=request.form.get('order_id')
        status=request.form.get('status')

        q=Order.query.get(id)
        q.status = status
        db.session.commit()
        return redirect(url_for('all_orders'))
    
@app.route('/admin_delete_order', methods = ["GET","POST"])
@login_required
@roles_accepted('Admin')
def admin_delete_order():
    if request.method == "GET" :
        order_id=request.args["order_id"]
        return render_template('confirm_delete_order_admin.html', order_id=order_id)
    
    if request.method == "POST" :
        order_id=request.form["order_id"]
        #delete order details from order_details table
        Order_Details.query.filter_by(order_id=order_id).delete()
        db.session.commit()

        #delete order from order table
        delete_order= Order.query.get(order_id)
        db.session.delete(delete_order)
        db.session.commit()
        #return'Order deleted Successfully'
        return redirect(url_for('all_orders'))


#Error Handler
@app.errorhandler(404)
def page_not_found(a):
    return render_template('404.html') , 404

@app.errorhandler(403)
def page_not_found(a):
    return render_template('403.html') , 403


####################################################################################################################
#API

from flask_restful import Resource, reqparse
from flask_restful import fields,marshal_with
from werkzeug.exceptions import HTTPException
from flask import make_response
import json
# from app import db, Catagory, Product

class NotFoundError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {"error_code":error_code, "error_message":error_message}
        self.response = make_response(json.dumps(message), status_code)

class BusinessValidationError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {"error_code":error_code, "error_message":error_message}
        self.response = make_response(json.dumps(message), status_code)

#output formate
output_fields = {
    "catagory_id":fields.Integer,
    "name" :fields.String,
    "description" : fields.String
}

#Create parser
create_parser = reqparse.RequestParser()
create_parser.add_argument('name')
create_parser.add_argument('description')

update_parser = reqparse.RequestParser()
update_parser.add_argument('name')
update_parser.add_argument('description')

#api class
class Categoryapi(Resource):
    @marshal_with(output_fields)
    def get(self, name):
        #get category name
        q = db.session.query(Catagory).filter(Catagory.name == name).first()

        if q:
            return q
        else: 
            raise NotFoundError(status_code=404, error_code= 104, error_message="category not found")
        
    def post(self):
        ar = create_parser.parse_args()
        n = ar.get("name", None)
        description = ar.get("description", None)

        if n is None:
            raise BusinessValidationError(status_code=400, error_code= 101, error_message="name is required" )

        if description is None:
            raise BusinessValidationError(status_code=400, error_code= 102, error_message="description is required" )
        
        query = db.session.query(Catagory).filter(Catagory.name == n).first()
        if query:
            raise BusinessValidationError(status_code=400, error_code= 103, error_message="duplicate name")
        
        new_category = Catagory(name = n, description = description)
        db.session.add(new_category)
        db.session.commit()
        return "Category is created", 201
    
    @marshal_with(output_fields)
    def put(self, name):
        #check if category exists
        q = db.session.query(Catagory).filter(Catagory.name == name).first()
        if q is None:
            raise NotFoundError(status_code=404, error_code= 104, error_message="category not found")
        
        #Geting name and description 
        ar = update_parser.parse_args()
        # update_name = ar.get("name", None)
        update_description = ar.get("description", None)

        #check if provided name for update is unique or not
        #check = db.session.query(Catagory).filter(Catagory.name == update_name).first()

        #if yes throw error 103
        # if check is not None:
        #     raise BusinessValidationError(status_code=400, error_code= 103, error_message="duplicate name")
        
        #update name and description
        #q.name = update_name
        q.description = update_description
        db.session.commit()
        return q
    
    def delete(self, name):
        #check if category exists
        q = db.session.query(Catagory).filter(Catagory.name == name).first()
        if q is None:
            raise NotFoundError(status_code=404, error_code= 104, error_message="category not found")
        
        #delete product associated with this category

        #Product.query.filter_by(catagory_id = q.catagory_id).delete()
        p = Product.query.filter_by(catagory_id = q.catagory_id).first()
        if p :
            raise BusinessValidationError(status_code=400, error_code= 105, error_message="Can't delete category. As there are product in this category")
    
        db.session.delete(q)
        db.session.commit()


        return "", 200
    
api.add_resource(Categoryapi, "/api/category", "/category/<string:name>")

if __name__ == '__main__':
    app.run(debug=True)