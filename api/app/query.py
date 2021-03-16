from app import app
from flask import render_template

@app.route('/query')
def queryPage():
    return render_template("index.html")