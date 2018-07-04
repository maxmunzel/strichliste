# strichliste
a simple tool to get rid of tally lists. Built to work with slow hardware and unreliable network. Based on python, flask and HTML5.

[![Screenshot](https://raw.githubusercontent.com/maxmunzel/strichliste/master/.images/screenshot.png)]()

## Getting Started

To get *strichliste* up and running you need python3 (with pip) and [flask](http://flask.pocoo.org). 


```bash
# install python3 and pip
sudo apt-get install python3-pip

git clone https://github.com/maxmunzel/strichliste.git
cd strichliste

# install python dependencies (may need sudo)
pip3 install flask flask-sqlalchemy eventlet whitenoise
python3 setup.py install

# start the server
cd strichliste
python3 strichliste.py --testing # start using a temporary(!) database

# now open http://localhost:5000/ in your browser of choice
```

## Configuring the Server

All relevant Option are set using command line arguments. For a quick overview run
```bash
$ python3 strichliste.py --help
usage: strichliste.py [-h] [-d] [-t] [--reset] [-p PORT] [--host HOST]
                      [-db DB] [-psk PSK]

Starts the selfhosting 'strichliste' server

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           enables Flasks debugger (don't ever set in
                        production!)
  -t, --testing         set, if you want to execute initialises in unit
                        testing mode
  --reset               if set, clears any records and initialises the
                        database with default values.
  -p PORT, --port PORT
  --host HOST
  -db DB, --dataBaseURI DB
  -psk PSK              The secret key to authenticate transactions with.
                        defaults to "" (empty string)
```

* `--dataBaseURI`
must be in a valid [SQLAlchemy Database URI](http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls). 
Defaults to an sqlite db at `/tmp/test.db`.

* if `-psk` is set, make sure to open `http://yourip:yourport/static/setpsk.html` on all clients and set it there, too.

## Modifying Data 

For the time being there's no User Interface to manipulate Data. As the underlying database model is fairly simple,
just use a generic SQL Browser to manipulate the raw Data. For Sqlite (the default) [this](http://sqlitebrowser.org) tool is 
pretty straight forward. Just open your database, manipulate tables `transactions`, `categories`, and `users` as you wish 
(don't forget to apply your changes) and reload the page in your browser.

## Generating Reports

One of the convenient features of *strichliste* is the ability to quickly generate billing reports. Simply visit `/balances`, choose a timeframe and get
each users expenses (calculated by the price of categories and how many marks they got). 

## Security

All Operations that modify Data have to be signed by getting a challenge from `/challenge` and calculating the SHA512 
of the request + the challenge + the PreShared Secret (PSK). See look [here](https://github.com/maxmunzel/strichliste/blob/bde0d14f3ccb58be8fb7450f5a59c9f7e0f8d31e/strichliste/strichliste.py#L240)
for details. This signature is then appended to the request url. `frontend.js` defines a utility function [`sign(string)`](https://github.com/maxmunzel/strichliste/blob/bde0d14f3ccb58be8fb7450f5a59c9f7e0f8d31e/strichliste/static/frontend.js#L10)
that returns signed versions of given urls.

This ensures that only parties in knowledge of the PSK may alter data. The PSK is stored in the clients HTML5 localstorage using [barn](https://github.com/arokor/barn). 

**To insure the key is not extracted using a man-in-the-middle attack, you have to run the server behind a reverse-proxy using HTTPS and [HSTS](https://en.wikipedia.org/wiki/HTTP_Strict_Transport_Security).**

## Todo

* Some images for this readme
* multiple Languages
* better tests
* more in-depth documentation

