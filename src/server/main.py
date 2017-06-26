import json
from datetime import datetime

from flask import Flask
from flask import render_template
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

from src.server.models import User, Category, Product, Transaction

app = Flask(__name__)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'


def init_with_dummy_data():
    db.drop_all()
    db.create_all()
    erik = User("Erik")
    monika = User("Monika")
    gerhard = User("Gerhard")
    bernd = User("Bernd")
    cat_a = Category("A", 0.4)
    cat_b = Category("B", 0.45)
    cat_c = Category("C", 0.8)
    cat_d = Category("D", 1.1)
    ötti = Product(name="Öttinger",
                   category=cat_b,
                   bulk_size=20)
    transaction_1 = Transaction(user=erik, category=cat_b, amount=5, timestamp=datetime.now(), undone=False)
    [db.session.add(entity) for entity in (erik, monika, gerhard, bernd, cat_a, cat_b, cat_c, cat_d, ötti, transaction_1)]
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
                     until_date: datetime=datetime.max):
    user = User.query.filter(User.id == user_id).first_or_404()
    return round(
                sum(
                    map(lambda x: x.price(),
                        get_transactions_of_user(from_date, until_date, user))
                )
            , 2)


def get_transactions_of_user(user, from_date, until_date):
    return list(  # for some reason this is needed
        Transaction.query.filter(Transaction.user == user,
                                 Transaction.undone == False,
                                 Transaction.timestamp > from_date,
                                 Transaction.timestamp < until_date).all()
    )


def get_number_of_purchases(user: User,
                            category: Category,
                            from_date: datetime = datetime.min,
                            until_date: datetime = datetime.max):
    transactions = get_transactions_of_user(user=user,
                                            from_date=from_date,
                                            until_date=until_date)
    return sum(
        map(lambda x: x.amount,
            filter(lambda transaction: transaction.category == category, transactions)
    )
    )

@app.route("/")
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


@app.route("/balances")
def balances():
    humans = list()

    [humans.append((user.name, str(get_user_balance(user.id)) + "€"))
     for user in User.query.order_by(User.name).all()]

    return render_template("backend.html",
                           humans=humans,
                           scaling="100%")  # ugly, semi-functional and currently only used for fiddling


@app.route("/add_transaction/<user_id>/<category_id>/<amount>")
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


@app.route("/get_user_balance/<user_id>")
def user_balance_wrapper(user_id):
    return str(get_user_balance(user_id))

@app.route("/get_number_of_purchases/<int:user_id>/<int:category_id>")
def number_of_purchases_wrapper(user_id: int, category_id: int):
    user = User.query.filter(User.id == user_id).first_or_404()
    category = Category.query.filter(Category.id == category_id).first_or_404()
    return str(get_number_of_purchases(user, category))


@app.route("/get_all_users")
def get_all_users():
    users = User.query.order_by(User.name).all()
    return jsonfy_users(users)


@app.route("/get_user_by_name/<name>")
def get_user_by_name(name: str):
    user = User.query.filter(User.name == name).first_or_404()
    return jsonfy_users([user])


@app.route("/add_user/<name>")
def add_user(name: str):
    user = User(name)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        return "{'Error': 'User with given name already exists'}"
    return jsonfy_users(user)

@app.route("/undo")
def undo():
    """Undoes the lastest (by time) transaction"""
    transaction = Transaction.query\
        .filter(Transaction.undone == False)\
        .order_by(Transaction.timestamp.desc()).first_or_404()
    transaction.undone = True
    db.session.add(transaction)
    db.session.commit()
    return "ok"


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)
if __name__ == "__main__":
    debug = True
    if debug:
        init_with_dummy_data()
    app.run(debug=debug, host="0.0.0.0")
