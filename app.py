from flask import Flask, request, render_template, redirect, url_for
from Request import Request

app = Flask(__name__)

@app.route('/', methods=["POST"])
def read_post():
    _request = Request(request.form["destination"], request.form["budget"], request.form["duration"])
    return redirect(url_for('map'))

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/')
def init():
    return render_template('index.html')