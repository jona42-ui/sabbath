import datetime
from symtable import SymbolTable
from xml.dom import NO_MODIFICATION_ALLOWED_ERR
from flask import Flask, render_template
import time
app = Flask(__name__)

@app.route("/")
@app.route("/home")
def index():
    now = datetime.datetime.now()
    sabbath_time = now.time==19 and now.day==7
    return render_template("index.html", sabbath_time=sabbath_time)

