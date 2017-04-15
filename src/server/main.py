from flask import Flask
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
import datetime

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
    price = db.Column(db.Float)

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


class ProductTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    user = db.relationship("User", backref="transactions")
    product = db.relationship("Product", backref="transactions")
    bulk = db.Column(db.Boolean)
    
    def __init_(self, user: User, product: Product, timestamp: datetime.datetime, bulk: bool = False) -> None:
        self.user = user
        self.product = product
        self.timestamp = timestamp
        self.bulk = bulk

    def get_size(self):
        # returns the number of articles in the transaction.
        if self.bulk:
            return self.product.bulk_size
        return 1


    def __repr__(self):
        return "<Transaction %r - %r>" % (self.user.name, self.product.name)

@app.route("/")
def hello():
    def get_user_data(user: User):
        output = list()
        output.append(user.name)
        # for category in Category.query.order_by(Category.price).all():
        #     output.append(sum(
        #         [transaction.get_size() for transaction in ProductTransaction.query.filter(user=user).filter(product.category=category).all()]
        #     ))
        return output


    data = dict()
    data["humans"] = list()
    data["fields"] = list()
    # data["humans"].append(["Dirk", 12, 1, 124, 0])
    # data["humans"].append(["Annika", 34, 23, 4, 0])
    # data["fields"] = ["Name", "Ö-Softdrinks", "Ö-Hell/Mate, Wasser", "Pils/Cola", "Weizen/Augustiner/Mate"]

    data["fields"].append("Name")
    for category_name in map(lambda x : x.name, Category.query.order_by(Category.price).all()):
        data["fields"].append(category_name)
    [data["humans"].append(get_user_data(user)) for user in User.query.order_by(User.name).all()]
    print (data["fields"])
    print(Category.query.all())
    return render_template("index.html", humans=data["humans"],
                           fields=data["fields"])


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
    transaction_1 = ProductTransaction(user=erik, product=ötti, timestamp=datetime.datetime.now())

    [db.session.add(entity) for entity in (erik, monika, gerhard, bernd, cat_b, cat_c, ötti, transaction_1)]
    db.session.commit()

if __name__ == "__main__":
    init_with_dummy_data()
    app.run(debug=True)

