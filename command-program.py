import os
import requests
from datetime import date, datetime

# ensure user provided api key and get key
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")
key = os.environ.get("API_KEY")

# same as lookup function in helpers.py, except there are 
# no limits on numbers of results and will find multiple 
# flights routes through same connection city
# commented in helpers.py
def lookup(origin, destination, departDate, returnDate=None):
    """Look up flight routes given dates and places"""
    
    if not returnDate:
        control = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&number_of_results=1&apikey={}".format(origin, destination, departDate, key))
        if control.status_code != 200:
            return None, None
        originalPrice = int(float(control.json()['results'][0]['fare']['total_price']))
        
        firstList = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/inspiration-search?origin={}&departure_date={}&one-way=true&max_price={}&apikey={}".format(origin, departDate, originalPrice-50, key))
        if firstList.status_code != 200:
            return None, None        
        
        flights = []
        for flight in firstList.json()['results']:
            code = flight['destination']
            firstMinPrice = int(float(flight['price']))
            second = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&max_price={}&apikey={}".format(code, destination, departDate, originalPrice-firstMinPrice, key))
            
            if second.status_code == 200:
                secondFlight = second.json()
                secondMinPrice = int(float(secondFlight['results'][0]['fare']['total_price']))
                first = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&max_price={}&apikey={}".format(origin, code, departDate, originalPrice-secondMinPrice, key))
                
                if first.status_code == 200:
                    firstFlight = first.json()
                    
                    for initial in firstFlight['results']:
                        firstPrice = int(float(initial['fare']['total_price']))
                        firstOutTime = datetime.strptime(initial['itineraries'][0]['outbound']['flights'][len(initial['itineraries'][0]['outbound']['flights'])-1]['arrives_at'], "%Y-%m-%dT%H:%M")
                        
                        for layover in secondFlight['results']:
                            secondPrice = int(float(layover['fare']['total_price']))
                            secondOutTime = datetime.strptime(layover['itineraries'][0]['outbound']['flights'][0]['departs_at'], "%Y-%m-%dT%H:%M")
                            
                            if (firstPrice + secondPrice < originalPrice and firstOutTime < secondOutTime):
                                city = requests.get("http://api.sandbox.amadeus.com/v1.2/location/{}/?apikey={}".format(code, key)).json()['city']['name']
                                flights.append({'city': city, 'price': firstPrice + secondPrice})
                            elif (firstPrice + secondPrice >= originalPrice):
                                break
                        
                        if (firstPrice + secondMinPrice >= originalPrice):
                            break
            
        if len(flights) == 0:
            return None, None
        else:
            results = sorted(flights, key=lambda flight: flight['price'])  
            return results, originalPrice
        
    else:
        control = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&return_date={}&number_of_results=1&apikey={}".format(origin, destination, departDate, returnDate, key))
        if control.status_code != 200:
            return None, None
        originalPrice = int(float(control.json()['results'][0]['fare']['total_price']))
        
        departD = date(int(departDate[:4]), int(departDate[5:7]), int(departDate[8:]))
        returnD = date(int(returnDate[:4]), int(returnDate[5:7]), int(returnDate[8:]))
        duration = (returnD - departD).days
        firstList = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/inspiration-search?origin={}&departure_date={}&duration={}&max_price={}&apikey={}".format(origin, departDate, duration, originalPrice-75, key))
        if firstList.status_code != 200:
            return None, None
        
        flights = []
        for flight in firstList.json()['results']:
            code = flight['destination']
            firstMinPrice = int(float(flight['price']))
            second = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&return_date={}&number_of_results=5&max_price={}&apikey={}".format(code, destination, departDate, returnDate, originalPrice-firstMinPrice, key))
            
            if second.status_code == 200:
                secondFlight = second.json()
                secondMinPrice = int(float(secondFlight['results'][0]['fare']['total_price']))
                first = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&return_date={}&max_price={}&number_of_results=5&apikey={}".format(origin, code, departDate, returnDate, originalPrice-secondMinPrice, key))
                
                if first.status_code == 200:
                    firstFlight = first.json()
                    
                    for initial in firstFlight['results']:
                        firstPrice = int(float(initial['fare']['total_price']))
                        firstOutTime = datetime.strptime(initial['itineraries'][0]['outbound']['flights'][len(initial['itineraries'][0]['outbound']['flights'])-1]['arrives_at'], "%Y-%m-%dT%H:%M")
                        firstInTime = datetime.strptime(initial['itineraries'][0]['inbound']['flights'][0]['departs_at'], "%Y-%m-%dT%H:%M")
                        
                        for layover in secondFlight['results']:
                            secondPrice = int(float(layover['fare']['total_price']))
                            secondOutTime = datetime.strptime(layover['itineraries'][0]['outbound']['flights'][0]['departs_at'], "%Y-%m-%dT%H:%M")
                            secondInTime = datetime.strptime(layover['itineraries'][0]['inbound']['flights'][len(layover['itineraries'][0]['inbound']['flights'])-1]['arrives_at'], "%Y-%m-%dT%H:%M")
                            
                            if (firstPrice + secondPrice < originalPrice and firstOutTime < secondOutTime and secondInTime < firstInTime):
                                city = requests.get("http://api.sandbox.amadeus.com/v1.2/location/{}/?apikey={}".format(code, key)).json()['city']['name']
                                flights.append({'city': city, 'price': firstPrice + secondPrice})
                            elif (firstPrice + secondPrice >= originalPrice):
                                break
                        
                        if (firstPrice + secondMinPrice >= originalPrice):
                            break
            
        if len(flights) == 0:
            return None, None
        else:
            results = sorted(flights, key=lambda flight: flight['price'])  
            return results, originalPrice


def combineOneWay(outResults, outPrice, inResults, inPrice, roundPrice):
    """Search combinations of one-way outbound and inbound alternate routes"""
    # if there are not one-way outbound or inbound routes, return None
    if outResults == None or inResults == None:
        return None
    # if there are both one-way outbound and inbound routes
    else: 
        # list of alternate routes
        routes = []
        # if the sum of the prices of the cheapest direct one-way flights
        # to and from you destination are less than the cheapest regular round-trip
        # flight, then those direct flights and any other flights in the
        # outbound and inbound sets of results must be cheaper than the regular round-trip
        # flights
        if outPrice + inPrice < roundPrice:
            # add all one-way outbound and inbound flights to route
            for outRoute in outResults:
                for inRoute in inResults:
                    routes.append({"outCity":outRoute['city'], "inCity": inRoute['city'], "price": int(outRoute['price']) + int(inRoute['price'])})
                    routes.append({"outCity":"direct", "inCity": inRoute['city'], "price": outPrice + int(inRoute['price'])})
                    routes.append({"outCity":outRoute['city'], "inCity": "direct", "price": int(outRoute['price']) + inPrice})
            routes.append({"outCity":"direct", "inCity": "direct", "price": outPrice + inPrice})
        else:
            # cheapest one-way inbound route
            inMinPrice = int(inResults[0]['price'])
            # iterate through all outbound routes
            for outRoute in outResults:
                # current outbound route price
                outPrice = int(outRoute['price'])
                # iterate through all inbound routes
                for inRoute in inResults:
                    # current inbound route
                    inPrice = int(inRoute['price'])
                    # if the sum of the current outbound and inbound route are less than
                    # the sum of the regular round-trip flight, add them to the list of routes
                    if (outPrice + inPrice < roundPrice):
                        routes.append({"outCity":outRoute['city'], "inCity": inRoute['city'], "price": outPrice + inPrice})
                    # otherwise breaks from the loop of inbound routes, since
                    # they will only get more expensive onward
                    else:
                        break
                # if the current outbound route plus the minimum inbound route
                # is greater than the regular round-trip price break out of the
                # entire loop, since the prices will only get higher from this point
                if (outPrice + inMinPrice >= roundPrice):
                    break
        return routes    


# get valid origin
while True:
    origin = input("Origin*: ")
    if origin:
        originCheck = requests.get("http://api.sandbox.amadeus.com/v1.2/location/{}/?apikey={}".format(origin, key))
        if originCheck.status_code == 200:
            break
# get valid destination      
while True:
    destination = input("Destination*: ")
    if destination:
        destinationCheck = requests.get("http://api.sandbox.amadeus.com/v1.2/location/{}/?apikey={}".format(destination, key))
        if destinationCheck.status_code == 200:
            break
# get valid departure date
while True:
    departDate = input("Departure Date* (YYYY-MM-DD): ")
    if departDate:
        try:
            departCheck = datetime.strptime(departDate, "%Y-%m-%d")
        except ValueError:
            departCheck = False
        if departCheck != False:
            break
# ensure return date is valid if provided
while True:
    returnDate = input("Return Date (YYYY-MM-DD): ")
    if returnDate:
        try:
            returnCheck = datetime.strptime(returnDate, "%Y-%m-%d")
        except ValueError:
            returnCheck = False
        if returnCheck != False:
            break
    else:
        break

# search one-way outbound routes (i.e. from origin to destination)
outResults, outPrice = lookup(origin, destination, departDate)

# if round-trip flight
if returnDate:
    # search one-way inbound rotes (i.e. from destination to origin)
    inResults, inPrice = lookup(destination, origin, returnDate)
    # search round-trip routes composed of round-trip flights
    # i.e. from origin to connection and back (eventually) and
    # from connection to destination and back (eventually)
    roundResults, roundPrice = lookup(origin, destination, departDate, returnDate)
    # search combinations of one-way outbound and inbound routes
    # i.e. routes from origin to destination and routes from destination to origin
    roundOneWay = combineOneWay(outResults, outPrice, inResults, inPrice, roundPrice)
    # if there are no results
    if roundResults == None and roundOneWay == None:
        print("Sorry, no cheaper round-trip routes")
    # otherwise print out results
    else:
        print("________________________")
        print("REGULAR PRICE: " + str(roundPrice))
        print("________________________")
        print(roundResults)
        print("________________________")
        print(roundOneWay)
# if a one-way flight        
else:
    # if there are no results
    if outResults == None:
        print("Sorry, no cheaper one-way routes")
    # if there are results, print them out
    else:
        print("\n")
        print("REGULAR PRICE: $" + str(outPrice))
        print("________________________")
        print("Alternate Routes:")
        print("\n")
        for result in outResults:
            print(result['city'] + ": $" + str(result['price']))
