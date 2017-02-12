import os
import requests
from datetime import date, datetime

from flask import render_template


def lookup(origin, destination, departDate, returnDate=None):
    """Look up alternate flight routes given dates and places"""
    
    key = os.environ.get("API_KEY")
    
    # if one-way search (all flights are one-way)
    if returnDate == None:
        # flight information for cheapest regular, single-airline flight with given origin, destination, departure date
        control = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&number_of_results=1&apikey={}".format(origin, destination, departDate, key))
        # check if a flight was returned
        if control.status_code != 200:
            return None, None
        # price of cheapest regular, single-airline flight
        originalPrice = int(float(control.json()['results'][0]['fare']['total_price']))
        
        # list of all destinations from origin cheaper than regular price of user-input destination
        # list of potential connection points
        firstList = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/inspiration-search?origin={}&departure_date={}&one-way=true&max_price={}&apikey={}".format(origin, departDate, originalPrice-50, key))
        # check if a flight was returned
        if firstList.status_code != 200:
            return None, None        
        
        # list of alternate flight routes from origin to destination
        flights = []
        # iterate through all potential connection points
        for flight in firstList.json()['results']:
            # potential connection point
            connection = flight['destination']
            # price of cheapest flight from origin to connection
            firstMinPrice = int(float(flight['price']))
            # list of cheapest flights from connection to destination
            second = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&max_price={}&number_of_results=5&apikey={}".format(connection, destination, departDate, originalPrice-firstMinPrice, key))
            # boolean true if current connection point already in list of alternate routes
            connectionFound = False
            # ensure a flight was found
            if second.status_code == 200:
                secondFlight = second.json()
                # price of cheapest flight from connection to destination
                secondMinPrice = int(float(secondFlight['results'][0]['fare']['total_price']))
                # list of cheapest flights from origin to connection
                first = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&max_price={}&number_of_results=5&apikey={}".format(origin, connection, departDate, originalPrice-secondMinPrice, key))
                # ensure a flight was found
                if first.status_code == 200:
                    firstFlight = first.json()
                    # iterate through first leg flights
                    for initial in firstFlight['results']:
                        # price of current flight from origin to connection
                        firstPrice = int(float(initial['fare']['total_price']))
                        # arrival time of current flight from origin to connection
                        firstOutTime = datetime.strptime(initial['itineraries'][0]['outbound']['flights'][len(initial['itineraries'][0]['outbound']['flights'])-1]['arrives_at'], "%Y-%m-%dT%H:%M")
                        # iterate through layover flights
                        for layover in secondFlight['results']:
                            # price of current flight from connection to destination
                            secondPrice = int(float(layover['fare']['total_price']))
                            # departure time of current flight from connection to destination
                            secondOutTime = datetime.strptime(layover['itineraries'][0]['outbound']['flights'][0]['departs_at'], "%Y-%m-%dT%H:%M")
                            # if the combined prices of current first leg flight and second leg flight are less than
                            # cheapest regular flight price and the first flight arrives before the second flight departs,
                            # add flight route to list of alternate, cheaper routes
                            if (firstPrice + secondPrice < originalPrice and firstOutTime < secondOutTime):
                                # get full city name of connection point
                                city = requests.get("http://api.sandbox.amadeus.com/v1.2/location/{}/?apikey={}".format(connection, key)).json()['city']['name']
                                # add flight route to list of alternate routes
                                flights.append({'city': city, 'price': firstPrice + secondPrice})
                                # current connection now in list of alternate flights
                                connectionFound = True
                                # break from loop of layover flights
                                break
                            # if the prices are already beyond regular flight price, break from loop of layover flights
                            elif (firstPrice + secondPrice >= originalPrice):
                                break
                        # if current first leg flight plus cheapest possible layover flight already beyond price
                        # of regular flight or if current connection point already added to list of routes,
                        # break from loop of current first leg flights (i.e. move to next potential connection point)
                        if (firstPrice + secondMinPrice >= originalPrice or connectionFound):
                            break           
        
        # return list of sorted flights and price of regular flight, if alternate routes exist
        if len(flights) == 0:
            return None, None
        else:
            # sort list of alternate routes by price
            sortedFlights = sorted(flights, key=lambda flight: flight['price'])  
            return sortedFlights, originalPrice
        
    # else round-trip search (all flights are round-trip)
    else:
        # flight information for cheapest regular, single-airline flight with given origin, destination, departure date
        control = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&return_date={}&number_of_results=1&apikey={}".format(origin, destination, departDate, returnDate, key))
        # check if a flight was returned
        if control.status_code != 200:
            return None, None
        # price of cheapest regular, single-airline flight
        originalPrice = int(float(control.json()['results'][0]['fare']['total_price']))
    
        # calculate difference between departure and return date in days
        departD = date(int(departDate[:4]), int(departDate[5:7]), int(departDate[8:]))
        returnD = date(int(returnDate[:4]), int(returnDate[5:7]), int(returnDate[8:]))
        duration = (returnD - departD).days
        
        # list of all destinations from origin cheaper to fly to than regular price of user-input destination
        # i.e. list of potential connection points
        firstList = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/inspiration-search?origin={}&departure_date={}&duration={}&max_price={}&apikey={}".format(origin, departDate, duration, originalPrice-75, key))
        # ensure a flight was returned
        if firstList.status_code != 200:
            return None, None
            
        # list of alternate flight routes from origin to destination (and back)
        flights = []
        # iterate through all potential connection points
        for flight in firstList.json()['results']:
            # potential connection point
            connection = flight['destination']
            # price of cheapest flight from origin to connection (and back)
            firstMinPrice = int(float(flight['price']))
            # list of cheapest flights from connection to destination (and back)
            second = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&return_date={}&max_price={}&number_of_results=5&apikey={}".format(connection, destination, departDate, returnDate, originalPrice-firstMinPrice, key))
            # boolean true if current connection point already in list of alternate routes
            connectionFound = False
            # ensure a flight was found
            if second.status_code == 200:
                secondFlight = second.json()
                # price of cheapest flight from connection to destination
                secondMinPrice = int(float(secondFlight['results'][0]['fare']['total_price']))
                # list of cheapest flights from origin to connection (and back)
                first = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&return_date={}&max_price={}&number_of_results=5&apikey={}".format(origin, connection, departDate, returnDate, originalPrice-secondMinPrice, key))
                # ensure a flight was found
                if first.status_code == 200:
                    firstFlight = first.json()
                    # iterate through first leg flights
                    # (first leg on outbound flight, second leg for inbound flight)
                    for initial in firstFlight['results']:
                        # price of current flight from origin to connection (and back)
                        firstPrice = int(float(initial['fare']['total_price']))
                        # arrival time of current flight from origin to connection
                        firstOutTime = datetime.strptime(initial['itineraries'][0]['outbound']['flights'][len(initial['itineraries'][0]['outbound']['flights'])-1]['arrives_at'], "%Y-%m-%dT%H:%M")
                        # departure time of current return flight from connection to origin
                        firstInTime = datetime.strptime(initial['itineraries'][0]['inbound']['flights'][0]['departs_at'], "%Y-%m-%dT%H:%M")
                        # iterate through second leg flights
                        # (second leg for outbound flight, first leg for inbound flight)
                        for layover in secondFlight['results']:
                            # price of current flight from connection to destination (and back)
                            secondPrice = int(float(layover['fare']['total_price']))
                            # departure time of current flight from connection to destination
                            secondOutTime = datetime.strptime(layover['itineraries'][0]['outbound']['flights'][0]['departs_at'], "%Y-%m-%dT%H:%M")
                            # arrival time of current return flight from destination to connection
                            secondInTime = datetime.strptime(layover['itineraries'][0]['inbound']['flights'][len(layover['itineraries'][0]['inbound']['flights'])-1]['arrives_at'], "%Y-%m-%dT%H:%M")
                            # if prices of current first leg plus second leg are less than original regular price
                            # and the outbound first flight arrives before outbound second flights departs 
                            # and inbound second flight arrives before inbound first flight departs
                            # add connection point to list of flight routes
                            if (firstPrice + secondPrice < originalPrice and firstOutTime < secondOutTime and secondInTime < firstInTime):
                                # full city name of current connection point
                                city = requests.get("http://api.sandbox.amadeus.com/v1.2/location/{}/?apikey={}".format(connection, key)).json()['city']['name']
                                # add connection point to list of flight routes
                                flights.append({'city': city, 'price': firstPrice + secondPrice})
                                # flight has been found for current connection point
                                connectionFound = True
                                # break from loop of layover flights
                                break
                            # if the prices are already beyond regular flight price, break from loop of layover flights
                            elif (firstPrice + secondPrice >= originalPrice):
                                break
                        
                        # if current first leg flight plus cheapest possible layover flight already beyond price
                        # of regular flight or if current connection point already added to list of routes,
                        # break from loop of current first leg flights (i.e. move to next potential connection point)
                        if (firstPrice + secondMinPrice >= originalPrice or connectionFound):
                            break
            
            
        # return list of sorted flights and price of regular flight, if alternate routes exist
        if len(flights) == 0:
            return None, None
        else:
            # sort list of alternate routes by price
            sortedFlights = sorted(flights, key=lambda flight: flight['price'])     
            return sortedFlights, originalPrice
    

def apology(top="", bottom=""):
    """Renders message as an apology to user."""
    """Taken from CS50 Pset 7 distribution code"""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
            ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=escape(top), bottom=escape(bottom))
    
# search combinations of one-way outbound and inbound alternate routes
# same function commented in command-program.py
## taken out of website
"""
def combineOneWay(outResults, outPrice, inResults, inPrice, roundPrice):
    
    if outResults == None or inResults == None:
        return None
    else: 
        routes = []
        if outPrice + inPrice < roundPrice:
            for outRoute in outResults:
                for inRoute in inResults:
                    routes.append({"cities":(outRoute['city'], inRoute['city']), "price": int(outRoute['price']) + int(inRoute['price'])})
        else:
            inMinPrice = int(inResults[0]['price'])
            for outRoute in outResults:
                outPrice = int(outRoute['price'])
                for inRoute in inResults:
                    inPrice = int(inRoute['price'])
                    if (outPrice + inPrice < roundPrice):
                        routes.append({"cities":(outRoute["city"], inRoute["city"]), "price": outPrice + inPrice})
                    else:
                        break
                if (outPrice + inMinPrice >= roundPrice):
                    break
        return routes    
"""