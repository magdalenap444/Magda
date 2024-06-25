import io
from datetime import datetime, timedelta
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app: Flask = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret-key'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now)
    date_updated = db.Column(db.DateTime, nullable=True)
    min_quantity = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(100), nullable=False)
    added_by = db.Column(db.String(100), nullable=False)
    updated_by = db.Column(db.String(100), nullable=True)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    details = db.Column(db.String(200), nullable=False)

    user = db.relationship('User', backref=db.backref('activities', lazy=True))
    product = db.relationship('Product', backref=db.backref('activities', lazy=True))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło', 'error')
    return render_template('login.html')


@app.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256',salt_length=8)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('signup.html')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś wylogowany', 'success')
    return redirect(url_for('signup'))
@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    error_message = None

    if request.method == 'POST':
        barcode = request.form['barcode']
        name = request.form['name']
        quantity = request.form['quantity']
        min_quantity = request.form['min_quantity']
        category = request.form['category']  # Pobranie wartości kategorii

        if not barcode or not name or not quantity or not min_quantity or not category:
            error_message = "Wszystkie pola są wymagane."
        elif int(quantity) < 0:
            error_message = "Nie można dodać produktu z ujemną ilością."
        elif not min_quantity.strip():
            error_message = "Musisz określić minimalny stan na magazynie."
        else:
            date_added = datetime.now()
            product = Product.query.filter_by(barcode=barcode).first()
            if product:
                product.quantity += int(quantity)
                product.date_updated = date_added
                product.min_quantity = int(min_quantity)
                product.category = category
                action = 'update'
            else:
                new_product = Product(
                    barcode=barcode,
                    name=name,
                    quantity=int(quantity),
                    date_added=date_added,
                    min_quantity=int(min_quantity),
                    category=category,
                    added_by=current_user.username
                )
                db.session.add(new_product)
                action = 'add'

            db.session.commit()


            log = ActivityLog(
                action=action,
                product_id=product.id if product else new_product.id,
                user_id=current_user.id,
                details=f"Barcode: {barcode}, Name: {name}, Quantity: {quantity}, Category: {category}"
            )
            db.session.add(log)
            db.session.commit()

            return redirect(url_for('inventory'))

    return render_template('add_product.html', error_message=error_message)


@app.route('/update', methods=['GET', 'POST'])
@login_required
def update_product():
    error_message = None
    if request.method == 'POST':
        barcode = request.form['barcode']
        quantity = request.form['quantity']
        date_updated = request.form['date_updated']
        operation = request.form['operation']

        if not barcode or not quantity or not date_updated or not operation:
            error_message = "Wszystkie pola są wymagane."
        elif operation not in ['add', 'remove']:
            error_message = "Niedozwolona operacja."
        else:
            product = Product.query.filter_by(barcode=barcode).first()

            if product:
                quantity = int(quantity)
                if operation == 'add':
                    product.quantity += quantity
                    action = 'add quantity'
                elif operation == 'remove' and product.quantity >= quantity:
                    product.quantity -= quantity
                    action = 'remove quantity'
                    if product.quantity == 0:
                        flash('Złóż zamówienie.', 'warning')
                else:
                    error_message = 'Nie można pobrać z magazynu danej ilości materiału.'

                if not error_message:
                    product.date_updated = datetime.strptime(date_updated, '%Y-%m-%dT%H:%M')
                    product.updated_by = current_user.username
                    db.session.commit()


                    log = ActivityLog(
                        action=action,
                        product_id=product.id,
                        user_id=current_user.id,
                        details=f"Barcode: {barcode}, Operation: {operation}, Quantity: {quantity}"
                    )
                    db.session.add(log)
                    db.session.commit()

                    return redirect(url_for('inventory'))
            else:
                error_message = 'Produkt nie istnieje.'

    return render_template('update_product.html', error_message=error_message)

@app.route('/activity_log')
@login_required
def activity_log():
    logs = ActivityLog.query.all()
    return render_template('activity_log.html', logs=logs)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#db.init_app(app)

@app.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        # Dodanie jednego dnia do daty końcowej, aby obejmować pełen zakres dnia
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
    except ValueError:
        return "Nieprawidłowy format daty. Użyj formatu YYYY-MM-DD.", 400


    logs = ActivityLog.query.filter(ActivityLog.timestamp >= start_date, ActivityLog.timestamp < end_date).all()

    # Sprawdź czy są jakieś dane do raportu
    if not logs:
        return "Brak danych do wygenerowania raportu w podanym zakresie dat.", 404

    # Tworzenie listy nagłówków i danych do zapisania w pliku CSV
    headers = ['Timestamp', 'Action', 'Product ID', 'User ID', 'Details']
    data = [[log.timestamp.strftime('%Y-%m-%d %H:%M:%S'), log.action, log.product_id, log.user_id, log.details] for log in logs]

    # Tworzenie pliku CSV w pamięci
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(data)

    # Ustawienie odpowiednich nagłówków dla odpowiedzi HTTP
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=activity_report.csv'

    return response

@app.route('/inventory')
@login_required
def inventory():
    products = Product.query.all()
    return render_template('inventory.html', products=products)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
