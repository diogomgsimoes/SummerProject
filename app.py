from flask import Flask, request, render_template
from Request import Request

app = Flask(__name__)

@app.route('/', methods=["POST"])
def read_post():
    _request = Request(request.form["destination"], request.form["budget"], request.form["duration"])
    return _request.__dict__

@app.route('/')
def init():
    return render_template('index.html')