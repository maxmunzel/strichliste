import os
import src.server as strichliste
import unittest
import tempfile

class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, strichliste.app.config['DATABASE'] = tempfile.mkstemp()
        strichliste.app.config['TESTING'] = True
        self.app = strichliste.app.test_client()
        with strichliste.app.app_context():
            strichliste.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(strichliste.server.app.config['DATABASE'])

    def test_something(self):
        # assert strichliste.
        pass


if __name__ == '__main__':
    unittest.main()
