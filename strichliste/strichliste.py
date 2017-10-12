import json
from datetime import datetime, timedelta

import eventlet
import argparse
import random
import hashlib
from string import ascii_letters
from flask import Flask
from flask import abort
from flask import current_app
from flask import render_template
from flask import request
from flask import send_from_directory

from models import db, User, Category, Product, Transaction

eventlet.monkey_patch()


# argument parsing
parser = argparse.ArgumentParser(description="Starts the selfhosting 'strichliste' server")
parser.add_argument(
    "-d", "--debug",
    action="store_true",
    help="enables Flasks debugger (don't ever set in production!)")
parser.add_argument(
    "-t", "--testing",
    action="store_true",
    help="set, if you want to execute strichliste in unit testing mode")
parser.add_argument(
    "--reset",
    action="store_true",
    help="if set, clears any records and initializes the database with default values.")
parser.add_argument(
    "-p", "--port",
    type=int,
    default=5000)
parser.add_argument(
    "--host",
    default="0.0.0.0")
parser.add_argument(
    "-db", "--dataBaseURI",
    dest="db",
    default="sqlite:////tmp/test.db"
)
parser.add_argument(
    "-psk",
    default="",
    help="The secret key to authenticate transactions with. defaults to \"\" (empty string)"
)
args = parser.parse_args()

DEBUG = args.debug                                  # default: False
TESTING = args.testing                              # default: False
RESET = args.reset                                  # default: False
PORT = args.port                                    # default: 5000
HOST = args.host                                    # default: "0.0.0.0"
SQLALCHEMY_DATABASE_URI = args.db                   # default: "sqlite:////tmp/test.db"
PSK = args.psk                                      # default: ""


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


create_app().app_context().push()


def init_with_dummy_data():
    assert TESTING or ("YES" == input("Are your sure to delete all records and reset the database? [YES/NO]"))
    db.drop_all()
    db.create_all()
    coleur = User("Coleur")
    cat_a = Category("A", 0.4)
    cat_b = Category("B", 0.45)
    cat_c = Category("C", 0.8)
    cat_d = Category("D", 1.1)
    ötti = Product(
        name="Öttinger",
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
                     from_date: datetime = datetime.min,
                     until_date: datetime = datetime.max) -> float:
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
               Transaction.query \
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


challenge = None


@current_app.route("/challenge")
def get_crypto_challenge():
    "returns the current challenge used to verify transactions. regenerate after *every* use."
    global challenge
    if challenge is None:
        challenge = "".join(random.SystemRandom().choice(ascii_letters) for _ in range(42))
    return challenge


def check_transaction(transaction: str, hash: str, psk: str = PSK) -> bool:
    """
    validates a transaction. afterwards discards the current challenge and generates a new one.
    a valid transaction hash is
        sha512(transaction+challenge+psk) as hexdigests.
    , with challenge being supplied by get_crypto_challenge() and the transaction string representing *all* properties
    of the transaction in a *unambiguous* way.
    """
    global challenge
    result = (hash == hashlib.sha512(str(transaction + get_crypto_challenge() + psk).encode("ascii")).hexdigest())
    challenge = "".join(random.SystemRandom().choice(ascii_letters) for _ in range(42))
    return result


@current_app.route("/add_transaction/<user_id>/<category_id>/<amount>/<checksum>")
def add_transaction(user_id: str, category_id: str, amount: int, checksum: str):
    valid = check_transaction(
        transaction="/add_transaction/" + user_id + "/" + category_id + "/" + str(amount),
        hash=checksum)

    if valid is False:
        abort(403)

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


@current_app.route("/add_user/<new_name>/<checksum>")
def add_user(new_name: str, checksum: str):
    if check_transaction("add_user/" + new_name, checksum) is False:
        abort(403)

    user = User(new_name)
    if User.query.filter(User.name == new_name).first() is not None:
        return "{'Error': 'User with given name already exists'}"
    db.session.add(user)
    db.session.commit()
    return "Success!"


@current_app.route("/undo/<checksum>")
def undo(checksum: str):
    """Undoes the latest (by time) transaction"""
    if check_transaction("undo", checksum) is False:
        abort(403)
    transaction = Transaction.query \
        .filter(Transaction.undone == False) \
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
    if RESET:
        init_with_dummy_data()
    current_app.run(debug=DEBUG, host=HOST, port=PORT)
