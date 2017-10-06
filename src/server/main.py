import json
from datetime import datetime, timedelta

from flask import Flask
from flask import render_template
from flask import send_from_directory
from flask import current_app
from flask import request
from flask import abort
from src.server.models import db, User, Category, Product, Transaction
import eventlet

eventlet.monkey_patch()


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

create_app().app_context().push()


def init_with_dummy_data():
    db.drop_all()
    db.create_all()
    coleur = User("Coleur")
    cat_a = Category("A", 0.4)
    cat_b = Category("B", 0.45)
    cat_c = Category("C", 0.8)
    cat_d = Category("D", 1.1)
    ötti = Product(name="Öttinger",
                   category=cat_b,
                   bulk_size=20)
    # transaction_1 = Transaction(user=erik, category=cat_b, amount=5, timestamp=datetime.now(), undone=False)
    [db.session.add(entity) for entity in (coleur, cat_a, cat_b, cat_c, cat_d, ötti)]
    db.session.commit()


def jsonfy_users(users):
    def extract_user_info(user: User):
        # we only want some fields as there are some SQLAlchemy-generated fields, we don't want to return.
        response = dict()
        response["id"] = user.id
        response["name"] = user.name
        response["locked"] = user.locked
        return response
    return json.dumps(list(map(extract_user_info, users)), sort_keys=True, indent=4)


def get_user_balance(user_id: int,
                     from_date: datetime=datetime.min,
                     until_date: datetime=datetime.max) -> float:
    user = User.query.filter(User.id == user_id).first_or_404()
    return round(
                sum(
                    map(lambda x: x.price(),
                        get_transactions_of_user(user=user,
                                                 from_date=from_date,
                                                 until_date=until_date))
                )
                , 2)


def get_transactions_of_user(user, from_date, until_date):
    return list(  # for some reason this is needed
        filter(lambda transaction: transaction.user_id == user.id,
               Transaction.query\
                   .filter(Transaction.undone == False,
                           Transaction.timestamp > from_date,
                           Transaction.timestamp < until_date)
                   .all()
               )
    )


def get_number_of_purchases(user: User,
                            category: Category,
                            from_date: datetime = datetime.min,
                            until_date: datetime = datetime.max) -> int:
    transactions = get_transactions_of_user(user=user,
                                            from_date=from_date,
                                            until_date=until_date)
    return sum(
        map(lambda x: x.amount,
            filter(lambda transaction: transaction.category == category, transactions)
    )
    )


@current_app.route("/")
def hello():
    def get_user_data(user: User):
        output = list()
        output.append(user)
        for category in Category.query.order_by(Category.price).all():
            output.append(
                sum(
                    list(map(lambda x: x.amount,
                        list(Transaction.query.filter(Transaction.category == category,
                                                      Transaction.user == user,
                                                      Transaction.undone == False))
                        ))
                )
            )
        return output

    data = dict()
    data["humans"] = list()
    data["fields"] = list()
    # data["humans"].append(["Dirk", 12, 1, 124, 0])
    # data["humans"].append(["Annika", 34, 23, 4, 0])
    # data["fields"] = ["Name", "Ö-Softdrinks", "Ö-Hell/Mate, Wasser", "Pils/Cola", "Weizen/Augustiner/Mate"]
    name_field = Category("Name", 42)
    name_field.name = "Name"
    data["fields"].append(name_field)
    for category in Category.query.order_by(Category.price).all():
        data["fields"].append(category)
    [data["humans"].append(get_user_data(user)) for user in User.query.order_by(User.name).all()]
    return render_template("index.html",
                           humans=data["humans"],
                           fields=data["fields"],
                           scaling="100%")  # ugly, semi-functional and currently only used for fiddling


@current_app.route("/balances")
def balances():
    # parse date constrains
    try:
        begin_date = datetime.strptime(request.args["begin"], "%Y-%m-%d")
    except:
        begin_date = datetime.min

    try:
        end_date = datetime.strptime(request.args["end"], "%Y-%m-%d")
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    except:
        end_date = datetime.max

    # fetch data and render template
    humans = list()
    [humans.append((user.name, str(get_user_balance(user.id, begin_date, end_date)) + "€"))
     for user in User.query.order_by(User.name).all()]

    return render_template("backend.html",
                           humans=humans,
                           scaling="100%")  # ugly, semi-functional and currently only used for fiddling


@current_app.route("/add_transaction/<user_id>/<category_id>/<amount>")
def add_transaction(user_id: str, category_id: str, amount: int):
    amount = int(amount)
    if amount < 1:
        return "oh you."
    user = User.query.filter(User.id == user_id).first_or_404()
    category = Category.query.filter(Category.id == category_id).first_or_404()
    transaction = Transaction(user=user,
                              category=category,
                              timestamp=datetime.now(),
                              amount=amount,
                              undone=False)
    db.session.add(transaction)
    db.session.commit()
    return "ok"


@current_app.route("/get_user_balance/<user_id>")
def user_balance_wrapper(user_id):
    return str(get_user_balance(user_id))


@current_app.route("/get_number_of_purchases/<int:user_id>/<int:category_id>")
def number_of_purchases_wrapper(user_id: int, category_id: int):
    user = User.query.filter(User.id == user_id).first_or_404()
    category = Category.query.filter(Category.id == category_id).first_or_404()
    return str(get_number_of_purchases(user, category))


@current_app.route("/get_all_users")
def get_all_users():
    users = User.query.order_by(User.name).all()
    return jsonfy_users(users)


@current_app.route("/get_user_by_name/<name>")
def get_user_by_name(name: str):
    user = User.query.filter(User.name == name).first_or_404()
    return jsonfy_users([user])


@current_app.route("/add_user/<new_name>")
def add_user(new_name: str):
    user = User(new_name)
    if User.query.filter(User.name == new_name).first() is not None:
        return "{'Error': 'User with given name already exists'}"
    db.session.add(user)
    db.session.commit()
    return "Success!"


@current_app.route("/undo")
def undo():
    """Undoes the lastest (by time) transaction"""
    transaction = Transaction.query\
        .filter(Transaction.undone == False)\
        .order_by(Transaction.timestamp.desc()).first_or_404()
    # don't undo changes that happened more than 20s in the past
    if transaction.timestamp + timedelta(0, 20) < datetime.now():
        abort(404)
    transaction.undone = True
    db.session.add(transaction)
    db.session.commit()
    return "ok"


@current_app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)
if __name__ == "__main__":
    debug = True
    if debug:
        init_with_dummy_data()
    current_app.run(debug=False, host="0.0.0.0")
