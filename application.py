
from symtable import SymbolTable
from xml.dom import NO_MODIFICATION_ALLOWED_ERR
from flask import Flask, flash, redirect, render_template, request, session, abort
from random import randint
import shabbos_web_class
import googleapi

app = Flask(__name__)
 
@app.route("/")
def index():
    #return name
    

    Candletime = shabbos_web_class.return_candletime_string()
    countdown = shabbos_web_class.time_remaining()
   


    return render_template(
        'index.html',**locals())
 
if __name__ == "__main__":
    app.run()