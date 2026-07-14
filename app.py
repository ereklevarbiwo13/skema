import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from sqlalchemy import text
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, FloatField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "skema-school-project-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///skema.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    specs = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(200), nullable=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    items = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RegisterForm(FlaskForm):
    username = StringField("მომხმარებლის სახელი", validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField("პაროლი", validators=[DataRequired(), Length(min=6, max=50)])
    phone = StringField(
        "ტელეფონი",
        validators=[
            DataRequired(),
            Length(min=9, max=15),
            Regexp(r"^\+?[0-9\s-]{9,15}$", message="ტელეფონი უნდა იყოს სწორი ფორმატის"),
        ],
    )
    address = TextAreaField("გადასაცემელი მისამართი", validators=[DataRequired(), Length(min=10, max=200)])
    submit = SubmitField("რეგისტრაცია")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("ეს მომხმარებლის სახელი უკვე გამოყენებულია.")


class LoginForm(FlaskForm):
    username = StringField("მომხმარებლის სახელი", validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField("პაროლი", validators=[DataRequired()])
    submit = SubmitField("შესვლა")


class CheckoutForm(FlaskForm):
    phone = StringField(
        "ტელეფონი",
        validators=[
            DataRequired(),
            Length(min=9, max=15),
            Regexp(r"^\+?[0-9\s-]{9,15}$", message="ტელეფონი უნდა იყოს სწორი ფორმატის"),
        ],
    )
    address = TextAreaField("მიწოდების მისამართი", validators=[DataRequired(), Length(min=10, max=200)])
    payment_method = SelectField(
        "გადახდის მეთოდი",
        choices=[("Cash on Delivery", "ნაღდი ანგარიშსწორება"), ("Card Payment", "ბარათით გადახდა")],
        validators=[DataRequired()],
    )
    submit = SubmitField("შეკვეთის დადასტურება")


class AdminProductForm(FlaskForm):
    name = StringField("პროდუქტის სახელი", validators=[DataRequired(), Length(min=3, max=120)])
    price = FloatField("ფასი", validators=[DataRequired()])
    specs = TextAreaField("სპეციფიკაციები", validators=[DataRequired(), Length(min=5, max=300)])
    submit = SubmitField("პროდუქტის დამატება")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_cart_count():
    cart = session.get("cart", {})
    total_items = sum(cart.values()) if cart else 0
    return {"cart_item_count": total_items}


def seed_products():
    products = [
        ("Arduino Uno R3", 27.0, "ATmega328P, 5V, 14 Digital I/O, 6 Analog, 16MHz", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTPG-wjM7Ouoqag9GnfCd7gHqB7Q925nhGb9-dEXimA-A&s=10"),
        ("Arduino Nano", 18.0, "ATmega328P, 5V, USB Mini, კომპაქტური ზომა", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6irN5Hm5F0Vl5OnM_NH0YURns3u-_dg5S-0Vc9XEFWQ&s=10"),
        ("Arduino Mega 2560", 65.0, "ATmega2560, 54 Digital I/O, 16 Analog, 16MHz", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQsExOnCFXeMICF1rfkRzaCZDgAY-MIWaQgzejC6PDSYw&s=10"),
        ("ESP32 DevKit", 32.0, "Wi-Fi, Bluetooth, Dual-Core, 240MHz", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS1EZaij2nyFiGJQXBWyfT4_jJp5McKPZM5FPC0U3qKBA&s=10"),
        ("ESP8266 NodeMCU", 22.0, "Wi-Fi, USB, 80MHz, Lua/Arduino მხარდაჭერა", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTDiEAunN0AIp-WnAKeq-2UHStXfkdiY0Ufo-bCH2Cfaw&s=10"),
        ("Breadboard 830", 12.0, "830 კონტაქტი, უსადუღებო მონტაჟი", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ58mz2S6W_ScS9T2fYJ2Nnhib7ihq-PA6yxqMcZaPB2A&s=10"),
        ("Breadboard Power Module", 10.0, "3.3V/5V, MB102", "https://encrypted-tbn0.gstatic.com/shopping?q=tbn:ANd9GcSwGShpkB3hRMWSWdT3PriZaO67cTWtsPs7prnxoZ9IAwPdo-dMwqEYA2fQc0nhpcSVbn5UQtKTZnBIvKpBxBBSbLOl45MNZ66dkoAgxbX-5Q42FPlN6CnpsDDy28Z8gTI1bWLL6w&usqp=CAc"),
        ("Jumper Wire (120 ც.)", 12.0, "Male-Male, Male-Female, Female-Female", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTgCw5lYNo_BF0invcv5bNBn5F_1WOXjTjMzPbTN_tyWg&s=10"),
        ("SG90 Servo Motor", 12.0, "180°, 4.8–6V, 1.8kg/cm", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSBP-IQwVpIhBMVKyvGoFYZQBkuHk_RNzNLOvUcaOOLZQ&s=10"),
        ("MG996R Servo", 28.0, "Metal Gear, 10kg/cm, 4.8–7.2V", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRygJE790KMJ-LrKnKgN7q_MrjC6F8biMq_lANDLietrw&s=10"),
        ("DC Gear Motor TT", 8.0, "3–6V, პლასტმასის რედუქტორი", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTt874FL88r_yP78pGuL1T2m8DjD215BQHoW0ZutO49LA&s=10"),
        ("Stepper Motor 28BYJ-48", 15.0, "5V, 64:1 გადაცემა", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTWjBze4uG9OsMXJmLCIAxwoEDDcpxjvvFYkLf3tclMSA&s=10"),
        ("ULN2003 Driver", 8.0, "Stepper Motor Driver", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRg4TpbwS7iZZZAZOj7396ROXyjEO4LSUNqiiXO_0mWlw&s=10"),
        ("L298N Motor Driver", 18.0, "Dual H-Bridge, 2A, 5–35V", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTn3z2hoZ5-RDTag-wi-jSLMyFupYcEDMHOWP9Xqq3dMw&s=10"),
        ("HC-SR04 Ultrasonic", 10.0, "2–400 სმ, 5V", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR1gMPQrcjZYhtkqNOTeGqerMRYoMK-SIxhIA_1bmabww&s=10"),
        ("DHT11", 9.0, "ტემპერატურა და ტენიანობა", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTVedX_DtWUt1ijhNJcpYcgvFZ2LIJhiLS9zUdTxR9nyA&s=10"),
        ("PIR Motion Sensor", 10.0, "5–20V, მოძრაობის დეტექცია", "https://encrypted-tbn3.gstatic.com/shopping?q=tbn:ANd9GcSPwoRdMhGQQoZQNYHyRAeosD5qy0kmeTYo-rBQUcPGh_7kDsCoK4CStCFSAjmra1KRjsezxqhVNhh44hWDHKWY6Y8Y-UP2z04J4-F3T_iy4rp3NU14Ed03Mmc&usqp=CAc"),
        ("Flame Sensor", 8.0, "ცეცხლის აღმოჩენა", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzwDLqDnrY8Ro815ErKFlJyVM0w6L6wcE5YzIP63VK6g&s=10"),
        ("Rain Sensor", 10.0, "წვიმის დეტექტორი", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS7J6kgd9B6BEPcbRpVC9Hl36oJCVIshFjSo7b7Ccw7DQ&s=10"),
        ("Soil Moisture Sensor", 9.0, "ნადაგის ტენიანობის გაზომვა", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHLs9X1bQyvknmqJpReZMtzAggQo78Gq_aN-yjZ5eK_A&s=10"),
        ("RFID RC522", 15.0, "13.56MHz, SPI", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQo9uwkX3EycbwrTP2vsTcY7Sj56wvPxBQgDaS3vt0Ceg&s=10"),
        ("Bluetooth HC-05", 20.0, "Bluetooth 2.0, Serial UART", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT3HBV7mPsIRJmlHQ8kCVhGWWI3Fh1jeusks5Et6NWjxg&s=10"),
        ("Relay Module 1 Channel", 10.0, "5V, 10A", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRWCfpDsiCPve3ANLhkNZdSsgmsSW8qRw9h0JNx7yIcNw&s=10"),
        ("LCD 1602 I2C", 18.0, "16×2 სიმბოლო, I2C", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQx7liHAh31A_oVGPrDnFpO34FZM3ltBzL4kCDDaD-0Ow&s=10"),
        ("OLED Display 0.96\"", 22.0, "128×64, I2C, OLED", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgtVLBjU1D46q3tXGqUSPeBC3PuzSdABj8zwwZ4W4Gfw&s=10"),
        ("Joystick Module", 8.0, "X/Y ღერძები, ღილაკი", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR3Rs1bEXicw_ZBED5p5ky4UCma0B0ad9Q6-gXU073iEg&s=10"),
        ("Sound Sensor", 8.0, "მიკროფონის მოდული", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRW9g5zXp8k7ukYm9CPMvieNpBbuGq9aOTfDebWTcE3CA&s=10"),
        ("Buzzer Module", 5.0, "3.3V–5V, აქტიური", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS6jTXu5EnejrYG6mFWO0du6aq4AyMFMy4flrlwsKD2QA&s=10"),
        ("Push Button", 1.0, "4 პინი, 12×12 მმ", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSpYaMZTthe9zfNhMfladx-nNJMePzLFzS_L5-4rK6SCQ&s=10"),
        ("Potentiometer 10K", 3.0, "10kΩ, 3 პინი", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQtKPmHk7IR1_bEfbhtIt6lid23QNvi86n4JKLgMOV8ww&s=10"),
    ]

    for name, price, specs, image in products:
        product = Product.query.filter_by(name=name).first()
        if product:
            product.price = price
            product.specs = specs
            product.image_filename = image
        else:
            db.session.add(Product(name=name, price=price, specs=specs, image_filename=image))
    db.session.commit()


def seed_admin_user():
    if User.query.filter_by(username="admin").first():
        return
    admin = User(
        username="admin",
        password_hash=generate_password_hash("admin123"),
        phone="+995555000000",
        address="თბილისი, TBC Education",
        is_admin=True,
    )
    db.session.add(admin)
    db.session.commit()


def ensure_schema():
    with app.app_context():
        db.create_all()
        inspector = db.inspect(db.engine)
        product_columns = {col["name"] for col in inspector.get_columns("product")}
        if "image_filename" not in product_columns:
            db.session.execute(text("ALTER TABLE product ADD COLUMN image_filename VARCHAR(200)"))
            db.session.commit()


with app.app_context():
    ensure_schema()
    seed_products()
    seed_admin_user()


@app.route("/")
def index():
    query = request.args.get("search", "").strip()
    sort = request.args.get("sort", "")
    if query:
        products_q = Product.query.filter(Product.name.ilike(f"%{query}%"))
    else:
        products_q = Product.query

    if sort == 'price_desc':
        products = products_q.order_by(Product.price.desc()).all()
    elif sort == 'price_asc':
        products = products_q.order_by(Product.price.asc()).all()
    else:
        products = products_q.order_by(Product.id).all()
    return render_template("index.html", products=products, query=query, sort=sort)


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    product_id = request.form.get("product_id")
    product = Product.query.get_or_404(int(product_id))
    cart = session.get("cart", {})
    cart[str(product.id)] = cart.get(str(product.id), 0) + 1
    session["cart"] = cart
    flash(f"{product.name} დაემატა კალათაში.", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/cart")
def cart():
    cart_data = session.get("cart", {})
    cart_items = []
    total = 0.0
    for product_id, qty in cart_data.items():
        product = Product.query.get(int(product_id))
        if product:
            cart_items.append({"product": product, "qty": qty})
            total += product.price * qty

    form = CheckoutForm()
    if current_user.is_authenticated:
        form.phone.data = current_user.phone
        form.address.data = current_user.address

    return render_template("cart.html", cart_items=cart_items, total=round(total, 2), form=form)


@app.route("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    flash("პროდუქტი ამოღებულია კალათიდან.", "info")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["POST"])
def checkout():
    form = CheckoutForm()
    cart_data = session.get("cart", {})
    cart_items = []
    total = 0.0
    for product_id, qty in cart_data.items():
        product = Product.query.get(int(product_id))
        if product:
            cart_items.append({"product": product, "qty": qty})
            total += product.price * qty

    if not cart_items:
        flash("კალათა ცარიელია.", "warning")
        return redirect(url_for("cart"))

    if form.validate_on_submit():
        username = current_user.username if current_user.is_authenticated else "guest"
        items_summary = "\n".join([f"{item['product'].name} x{item['qty']}" for item in cart_items])
        order = Order(
            username=username,
            phone=form.phone.data,
            address=form.address.data,
            payment_method=form.payment_method.data,
            total_price=round(total, 2),
            items=items_summary,
        )
        db.session.add(order)
        db.session.commit()
        session["cart"] = {}
        flash("შეკვეთა წარმატებით მიღებულია!", "success")
        return redirect(url_for("index"))

    flash("ფორმა არ არის სწორად შევსებული.", "danger")
    return render_template("cart.html", cart_items=cart_items, total=round(total, 2), form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            password_hash=generate_password_hash(form.password.data),
            phone=form.phone.data,
            address=form.address.data,
            is_admin=False,
        )
        db.session.add(user)
        db.session.commit()
        flash("რეგისტრაცია წარმატებით დასრულდა!", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("შესვლა წარმატებით განხორციელდა.", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))
        flash("არასწორი მომხმარებლის სახელი ან პაროლი.", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("წარმატებით გამოხვალეთ.", "info")
    return redirect(url_for("index"))


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)

    form = AdminProductForm()
    if form.validate_on_submit():
        product = Product(name=form.name.data.strip(), price=form.price.data, specs=form.specs.data.strip())
        db.session.add(product)
        db.session.commit()
        flash("ახალი კომპონენტი დაემატა.", "success")
        return redirect(url_for("admin"))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin.html", form=form, orders=orders)


if __name__ == "__main__":
    app.run(debug=True)
