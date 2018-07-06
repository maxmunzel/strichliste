import unittest
import requests
import sys
import hashlib
import json
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from time import sleep
from subprocess import Popen, DEVNULL
import signal
import os

HOST = "http://localhost:5000/" # don't forget the trailing slash
PSK = ""


# before executing the tests, open strichliste in testing mode
class MyTestCase(unittest.TestCase):
    @staticmethod
    def sign(url):
        # signs the request url by appending a correct checksum
        r = requests.get(HOST+"challenge")
        challenge = r.text
        response = hashlib.sha512((url + challenge + PSK).encode("utf-8")).hexdigest()
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
    @staticmethod
    def get_user_by_name(name):
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

    def test_unicode_user(self):
        # can the system handle unicode users?
        username = "Sören 😀"
        self.add_user(username)
        user_id = self.get_user_by_name(username)
        self.send_transaction(user=user_id)
        n = self.get_number_of_purchases(user_id)
        self.assertEqual(n, "1")

    def send_transaction(self, user=1, category=1, amount=1):
        r = requests.get(HOST[:-1] + self.sign("/add_transaction/" + str(user) + "/" + str(category) + "/" + str(amount)))
        # self.assertEqual(r.status_code, 200)

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

    def test_negative_transaction(self):
        self.send_transaction()
        self.assertEqual(self.get_number_of_purchases(), "1", "system didn't accepted legit transaction")
        self.send_transaction(amount=-1)
        self.assertEqual(self.get_number_of_purchases(), "1", "system accepted negative amount in transaction")

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
        self.assertEqual(self.undo(), 200, "undo got rejected even though it was in time")
        self.assertEqual(self.get_number_of_purchases(), "1", "undo actually din't undo anything")
        sleep(2.5)
        self.assertEqual(self.undo(), 404, "undo got accepted even if it was out of time")
        self.assertEqual(self.get_number_of_purchases(), "1", "undo got rejected, but still removed transaction")

    def test_undo_valid(self):
        # do I actually need a correct token?
        random_checksum = "bebfbcb9f8b63c327c2392ab9be9a93f9e39611e212c3b4ae" \
                          "f12eb988eb8a9ef7a031ebe652fc4f1f1abc1c6775625688c6bc9300a48ed6861fb39c2f7a74c50"
        r = requests.get(HOST + "undo/" + random_checksum)
        self.assertEqual(r.status_code, 403, "Incorrect signature accepted for /undo!")

    def test_chrome_buffering(self):
        # tests basic functionality of the client side code including filling the buffer and reloading while syncing

        NUM_TRANSACTIONS = 184

        options = Options()
        options.headless = True
        chrome = Chrome(options=options)
        self.addCleanup(chrome.close)
        chrome.get(HOST)
        btn = chrome.find_element_by_id("bt-1%1")
        self.assertEqual(btn.text, "0", "User coleur should not have transactions yet, but counter is not '0'.")
        for i in range(NUM_TRANSACTIONS):
            btn.click()
        self.assertEqual(str(NUM_TRANSACTIONS), btn.text, "Button didn't count up.")
        sleep(0.5)
        # chrome.refresh()  # does the buffer survive reloads? (it doesn't always yet -.-)
        # wait until all transactions are transmitted or no new ones are arriving
        old = -1
        new = 0
        while old < new:
            sleep(0.5)
            old, new = int(new), int(self.get_number_of_purchases())

        self.assertEqual(NUM_TRANSACTIONS, int(self.get_number_of_purchases()), "Number of recieved transactions is wrong.")
        # we expect the interface to lie about buffered transaction to not surprise the user, so we have to refresh
        # now to get the actual number of transactions again (maybe fix this temporarily false display in the future?)
        chrome.refresh()
        btn = chrome.find_element_by_id("bt-1%1")
        self.assertEqual(str(NUM_TRANSACTIONS), btn.text, "Button shows wrong number of Transactions.")

if __name__ == '__main__':
    server = Popen("python3 ../strichliste.py --testing".split(" "), shell=False, stdout=DEVNULL, stderr=DEVNULL)
    sleep(1)
    try:
        unittest.main()
    finally:
        try:
            stop = requests.get(HOST + "stop")
        except:
            pass




