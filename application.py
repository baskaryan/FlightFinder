import os
import requests

from flask import Flask, flash, render_template, request, session
from flask_session import Session
from tempfile import gettempdir
from datetime import datetime

from helpers import *

# configure application
app = Flask(__name__)


# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response


# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/", methods=["GET", "POST"])
def search():
    """ Search for cheapest flight routes from point A to point B """
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        if not os.environ.get("API_KEY"):
            raise RuntimeError("API_KEY not set")
        key = os.environ.get("API_KEY")
        
        # get flight search parameters from user
        # ensure valid parameters given
        origin = request.form.get("origin")
        if not origin:
            return apology("Must enter origin")
        originCheck = requests.get("http://api.sandbox.amadeus.com/v1.2/location/{}/?apikey={}".format(origin, key))
        if originCheck.status_code != 200:
            return apology("Invalid origin")
            
        destination = request.form.get("destination")
        if not destination:
            return apology("Must enter destination")
        destinationCheck = requests.get("http://api.sandbox.amadeus.com/v1.2/location/{}/?apikey={}".format(destination, key))
        if destinationCheck.status_code != 200:
            return apology("Invalid destination")
            
        departDate = request.form.get("depart")
        if not departDate:
            return apology("Must enter departure date")
        try:
            departCheck = datetime.strptime(departDate, "%Y-%m-%d")
        except ValueError:
            departCheck = False
        if not departCheck:
            return apology("Invalid departure date")
        
        returnDate = request.form.get("returnDate")
        if returnDate:
            try:
                returnCheck = datetime.strptime(returnDate, "%Y-%m-%d")
            except ValueError:
                returnCheck = False
            if not returnCheck:
                return apology("Invalid return date")
        
        # search one-way outbound flights (i.e. from origin to destination)
        # taken out of website
        ##outResults, outPrice = lookup(origin, destination, departDate)
        
        # if there is a return date search round trip flights
        if returnDate:
            # search one-way inbound flights (i.e. from destination to origin)
            # taken out of website
            ##inResults, inPrice = lookup(destination, origin, returnDate)
            
            roundResults, roundPrice = lookup(origin, destination, departDate, returnDate)
            
            # search combinations of one-way outbound and inbound alternate routes
            # taken out of website
            ##roundOneWay = combineOneWay(outResults, outPrice, inResults, inPrice, roundPrice)
            
            # if there are no results return an apology
            if roundResults == None: #and (inResults == None or outResults == None):
                return apology("No cheaper flight routes")
            # return round trip routes
            else:
                # return template with both combinations of round trip flights and one-way flights
                # taken out of website
                ##return render_template("roundResults.html", roundResults=roundResults, price=roundPrice, oneResults=roundOneWay)
                
                # return template with combinations of reound trip flights
                return render_template("results.html", results=roundResults, price=roundPrice)
        
        # else if there is no return date consider only the outgoing one-way results
        else:
            # search one-way outgoing flights (i.e. from origin to destination)
            outResults, outPrice = lookup(origin, destination, departDate)
            
            # if there are no results return an apology
            if outResults == None:
                return apology("No cheaper one-way flight routes")
            # otherwise return the results
            else:
                return render_template("results.html", results=outResults, price=outPrice)
    
    # if user reached route via GET method simply render search html    
    else:
        return render_template("search.html")
