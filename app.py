from flask import Flask, request
from Request import Request

app = Flask(__name__)

@app.route('/', methods=["POST"])
def read_post():
    _request = Request(request.form["destination"])
    _request.test()
    return request.form["destination"]

@app.route('/')
def init():
    return """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Plan your trip</title>
</head>

<body>
<h1>Plan your trip</h1>
<form method="POST">
    <input name="destination">
    <input type="submit">
</form>

</body>
</html>"""