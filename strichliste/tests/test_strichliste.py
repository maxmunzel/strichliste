import unittest
import requests
import sys
import hashlib
import json
from time import sleep

HOST = "http://localhost:1847/" # don't forget the trailing slash
PSK = "nougat"


# before executing the tests, open strichliste in testing mode
class MyTestCase(unittest.TestCase):

    def sign(self, url):
        # signs the request url by appending a correct checksum
        r = requests.get(HOST+"challenge")
        challenge = r.text
        # url = url.replace(" ", "%20")
        response = hashlib.sha512(str(url + challenge + PSK).encode("ascii")).hexdigest()
        return url + "/" + response

    def setUp(self):
        # every test should run on a fresh db.
        r = requests.get(HOST+"reset")
        if r.status_code != 200:
            print("Strichliste does not seem to be in testing mode, aborting!")
            sys.exit(1)

    def test_reset(self):
        # check, that the initial conditions after a reset are as expected
        r = requests.get(HOST + "get_all_users")
        self.assertEqual(r.status_code, 200, "internal Error while requesting user list")
        users = json.loads(r.text)
        expected = [{'id': 1, 'locked': False, 'name': 'Coleur'}]
        self.assertEqual(users, expected, "expected exactly one user: Coleur")

        for i in range(4):
            r = requests.get(HOST + "get_number_of_purchases/1/" + str(i + 1))
            self.assertEqual(r.status_code, 200, "category " + str(i + 1) + " missing")
            self.assertEqual(r.text, "0", "there' a unexpected transaction in category " + str(i + 1) + "after reset.")

    def test_basic(self):
        # check if the basic interfaces get served
        for site in ("", "balances", "static/setpsk.html", "challenge"):
            r = requests.get(HOST)
            self.assertEqual(r.status_code, 200)

    def test_default_user(self):
        r = requests.get(HOST+"get_all_users")
        self.assertEqual(r.status_code, 200, "internal Error while requesting user list")
        users = json.loads(r.text)
        expected = [{'locked': False, 'id': 1, 'name': 'Coleur'}]
        self.assertEqual(users, expected, "DB should always contain user \"Coleur\"")

    def test_add_user(self):
        # tests if adding users works

        # add new user
        username = "test seems good right here!"
        self.add_user(username)

        # check if user actually shows up
        r = requests.get(HOST + "get_all_users")
        self.assertEqual(r.status_code, 200, "internal Error while requesting user list")
        users = json.loads(r.text)
        expected = [{'id': 1, 'locked': False, 'name': 'Coleur'},
                    {'id': 2, 'locked': False, 'name': 'test seems good right here!'}]
        self.assertEqual(users, expected, "get_all_users doesn't contain "+username)
        r = requests.get(HOST + "get_user_by_name/" + username)
        self.assertEqual(r.status_code, 200, "couldn't query new user by name")
        id = json.loads(r.text)[0]["id"]
        self.assertEqual(id, 2, "new user has unexpected id.")

    def get_user_by_name(self, name):
        r = requests.get(HOST + "get_user_by_name/" + name)
        id = json.loads(r.text)[0]["id"]
        return id

    def add_user(self, name):
        r = requests.get(HOST + self.sign("add_user/" + name))
        self.assertEqual(r.status_code, 200)
        return self.get_user_by_name(name)

    def test_add_user_valid(self):
        # do I actually need a correct token?
        username = "im a little fishy"
        random_checksum = "bebfbcb9f8b63c327c2392ab9be9a93f9e39611e212c3b4ae" \
                          "f12eb988eb8a9ef7a031ebe652fc4f1f1abc1c6775625688c6bc9300a48ed6861fb39c2f7a74c50"
        r = requests.get(HOST + "add_user/" + username + "/"+ random_checksum)
        self.assertEqual(r.status_code, 403, "Incorrect signature accepted!")

    def send_transaction(self, user=1, category=1, amount=1):
        r = requests.get(HOST[:-1] + self.sign("/add_transaction/" + str(user) + "/" + str(category) + "/" + str(amount)))
        self.assertEqual(r.status_code, 200)

    @staticmethod
    def get_number_of_purchases(user=1) -> str:
        r = requests.get(HOST + "get_number_of_purchases/" + str(user) + "/1")
        return r.text

    def test_transaction(self):
        user = self.add_user("sgnsor sr sjdf s")
        number_of_requests = 100
        for i in range(number_of_requests):
            self.send_transaction(user=user, amount=42)
        n = self.get_number_of_purchases(user)
        self.assertEqual(n, str(number_of_requests*42))

    def test_transaction_valid(self):
        # do I actually need a correct token?
        random_checksum = "bebfbcb9f8b63c327c2392ab9be9a93f9e39611e212c3b4ae" \
                          "f12eb988eb8a9ef7a031ebe652fc4f1f1abc1c6775625688c6bc9300a48ed6861fb39c2f7a74c50"
        r = requests.get(HOST + "add_transaction/1/1/1/" + random_checksum)
        self.assertEqual(r.status_code, 403, "Incorrect signature accepted!")

    def undo(self):
        r = requests.get(HOST + self.sign("undo"))
        return r.status_code

    def test_undo(self):
        timeout = 20
        for i in range(3):
            self.send_transaction(amount=1)
        self.assertEqual(self.undo(), 200, "undo got rejected for no apparent reason")
        self.assertEqual(self.get_number_of_purchases(), "2", "undo actually din't undo anything")
        sleep(timeout - 2)
        self.assertEqual(self.undo(), 200, "undo got rejected even if it was in time")
        self.assertEqual(self.get_number_of_purchases(), "1", "undo actually din't undo anything")
        sleep(2.5)
        self.assertEqual(self.undo(), 404, "undo got accepted even if it was out of time")
        self.assertEqual(self.get_number_of_purchases(), "1", "undo got rejected, but still removed transaction")

    def undo_valid(self):
        # do I actually need a correct token?
        random_checksum = "bebfbcb9f8b63c327c2392ab9be9a93f9e39611e212c3b4ae" \
                          "f12eb988eb8a9ef7a031ebe652fc4f1f1abc1c6775625688c6bc9300a48ed6861fb39c2f7a74c50"
        r = requests.get(HOST + "undo/" + random_checksum)
        self.assertEqual(r.status_code, 403, "Incorrect signature accepted!")

if __name__ == '__main__':
    unittest.main()
