import datetime
from symtable import SymbolTable
from xml.dom import NO_MODIFICATION_ALLOWED_ERR
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    now = datetime.datetime.now()
    sabbath_time = now.time==19 and now.day==6
    return render_template("index.html", sabbath_time=sabbath_time)

