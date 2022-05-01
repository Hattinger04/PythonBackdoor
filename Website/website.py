import os
from flask import Flask, send_file

app = Flask(__name__)
file = "/website.py"
path = os.path.dirname("./download'") + file


@app.route("/")
def homepage():
    return '<a href="/download">Download file<a>'


@app.route('/download', methods=["GET", "POST"])
def downloadFile():
    try:
        return send_file(path, as_attachment=True)
    except Exception as e:
        return str(e)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
