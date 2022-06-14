from flask import Flask, request, render_template
from Request import Request

app = Flask(__name__)

@app.route('/', methods=["POST"])
def read_post():
    _request = Request(request.form["destination"])
    _request.test()
    return request.form["destination"]

@app.route('/')
def init():
    return render_template('index.html')