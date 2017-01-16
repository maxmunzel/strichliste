from flask import Flask
from flask import render_template
app = Flask(__name__)

@app.route("/")
def hello():
    placeholder_data = dict()
    placeholder_data["humans"] = list()
    placeholder_data["humans"].append(["Dirk", 12, 1, 124, 0])
    placeholder_data["humans"].append(["Annika", 34, 23, 4, 0])
    placeholder_data["humans"].append(["Erik", 0, 2134, 0, 0])
    placeholder_data["fields"] = ["Name", "Ö-Softdrinks", "Ö-Hell/Mate, Wasser", "Pils/Cola", "Weizen/Augustiner/Mate"]

    return render_template("index.html", humans=placeholder_data["humans"]*20,
                           fields=placeholder_data["fields"])

if __name__ == "__main__":
    app.run(debug=True)