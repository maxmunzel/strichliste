from datetime import datetime

from src.server.main import db


class User(db.Model):
    # models a user by their name.
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    locked = db.Column(db.Boolean, nullable=False)

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
    name = db.Column(db.Text, unique=True, nullable=False)
    bulk_size = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    category = db.relationship("Category", backref="products")

    def __init__(self, name: str, category: Category, bulk_size: int = 0):
        self.name = name
        self.bulk_size = bulk_size
        self.category = category

    def __repr__(self):
        return "<Product %r>" % self.name


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    user = db.relationship("User", backref="transactions")
    category = db.relationship("Category", backref="transactions")
    amount = db.Column(db.Integer, nullable=False)
    undone = db.Column(db.Boolean, nullable=False)

    def __init_(self, user: User, category: Category, timestamp: datetime, amount: int = 1) -> None:
        self.undone = False
        self.user = user
        self.category = category
        self.timestamp = timestamp
        self.amount = amount

    def price(self):
        return self.category.price * self.amount

    def __repr__(self):
        return "<Transaction %r - %r>" % (self.user.name, self.product.name)