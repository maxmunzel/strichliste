from flask import Flask
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
import datetime
import json
from sqlalchemy.exc import IntegrityError
app = Flask(__name__)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'


def getData(user_id: str) -> object:
    pass


class User(db.Model):
    # models a user by their name.
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    locked = db.Column(db.Boolean)

    def __init__(self, name):
        self.name = name
        self.locked = False

    def __repr__(self):
        return '<User %r>' % self.name


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.Text, unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

    def __repr__(self):
        return "<Category %r>" % self.name


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    bulk_size = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    category = db.relationship("Category", backref="products")

    def __init__(self, name: str, category: Category, bulk_size: int = 0):
        self.name = name
        self.bulk_size = bulk_size
        self.category = category

    def __repr__(self):
        return "<Product %r>" % self.name


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    user = db.relationship("User", backref="transactions")
    category = db.relationship("Category", backref="transactions")
    amount = db.Column(db.Integer)

    def __init_(self, user: User, category: Category, timestamp: datetime.datetime, amount: int = 1) -> None:
        self.user = user
        self.category = category
        self.timestamp = timestamp
        self.amount = amount

    def __repr__(self):
        return "<Transaction %r - %r>" % (self.user.name, self.product.name)




def init_with_dummy_data():
    db.drop_all()
    db.create_all()
    erik = User("Erik")
    monika = User("Monika")
    gerhard = User("Gerhard")
    bernd = User("Bernd")
    cat_b = Category("B", 0.4)
    cat_c = Category("C", 0.8)
    ötti = Product(name="Öttinger",
                   category=cat_b,
                   bulk_size=20)
    transaction_1 = Transaction(user=erik, category=cat_b, amount=5, timestamp=datetime.datetime.now())
    [db.session.add(entity) for entity in (erik, monika, gerhard, bernd, cat_b, cat_c, ötti, transaction_1)]
    db.session.commit()

def jsonfy_user(user: User):
    response = dict()
    response["id"] = user.id
    response["name"] = user.name
    response["locked"] = user.locked
    return json.dumps(response, sort_keys=True, indent=4)

@app.route("/")
def hello():
    def get_user_data(user: User):
        output = list()
        output.append(user)
        for category in Category.query.order_by(Category.price).all():
            output.append(
                sum(
                    list(map(lambda x: x.amount,
                        list(Transaction.query.filter(Transaction.category == category, Transaction.user == user))
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
    return render_template("index.html", humans=data["humans"],
                           fields=data["fields"])


@app.route("/add_transaction/<user_id>/<category_id>/<amount>")
def add_transaction(user_id: str, category_id: str, amount: int):
    amount = int(amount)
    if amount < 1:
        return "oh you."
    user = User.query.filter(User.id == user_id).first_or_404()
    category = Category.query.filter(Category.id == category_id).first_or_404()
    transaction = Transaction(user=user, category=category, timestamp=datetime.datetime.now(), amount=amount)
    db.session.add(transaction)
    db.session.commit()
    return "ok"


@app.route("/get_user_by_name/<name>")
def get_user_by_name(name: str):
    user = User.query.filter(User.name == name).first_or_404()
    return jsonfy_user(user)


@app.route("/add_user/<name>")
def add_user(name: str):
    user = User(name)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        return "{'Error': 'User with given name already exists'}"
    return jsonfy_user(user)

if __name__ == "__main__":
    debug = True
    if debug:
        init_with_dummy_data()
    app.run(debug=debug)
