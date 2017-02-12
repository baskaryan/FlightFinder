from datetime import date, datetime
import requests

 
origin = "CLE"
destination = "NYC"
departDate = "2016-12-27"

control = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&number_of_results=1&apikey=4kLFYfEgqIjGCLli8wtsKYYOAZJG4QCg".format(origin, destination, departDate))

originalPrice = int(float(control.json()['results'][0]['fare']['total_price']))
firstList = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/inspiration-search?origin={}&departure_date={}&one-way=true&max_price={}&apikey=4kLFYfEgqIjGCLli8wtsKYYOAZJG4QCg".format(origin, departDate, originalPrice-50))
    
        
flights = []
for flight in firstList.json()['results']:
    code = flight['destination']
    firstMinPrice = int(float(flight['price']))
    second = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&max_price={}&apikey=4kLFYfEgqIjGCLli8wtsKYYOAZJG4QCg".format(code, destination, departDate, originalPrice-firstMinPrice))
    if second.status_code == 200:
        secondFlight = second.json()
        secondMinPrice = int(float(secondFlight['results'][0]['fare']['total_price']))
        #outArriveTime = secondFlight['results'][0]['itineraries'][len(secondFlight['results'][0]['itineraries'])-1]['outbound']['flights'][0]['departs_at']
        first = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&max_price={}&apikey=4kLFYfEgqIjGCLli8wtsKYYOAZJG4QCg".format(origin, code, departDate, originalPrice-secondMinPrice))
        if first.status_code == 200:
            firstFlight = first.json()
            for initial in firstFlight['results']:
                firstPrice = int(float(initial['fare']['total_price']))
                firstOutTime = datetime.strptime(initial['itineraries'][0]['outbound']['flights'][len(initial['itineraries'][0]['outbound']['flights'])-1]['arrives_at'], "%Y-%m-%dT%H:%M")
                for layover in secondFlight['results']:
                    secondPrice = int(float(layover['fare']['total_price']))
                    secondOutTime = datetime.strptime(layover['itineraries'][0]['outbound']['flights'][0]['departs_at'], "%Y-%m-%dT%H:%M")
                    if (firstPrice + secondPrice < originalPrice and firstOutTime < secondOutTime):
                        city = requests.get("http://api.sandbox.amadeus.com/v1.2/location/{}/?apikey=4kLFYfEgqIjGCLli8wtsKYYOAZJG4QCg".format(code)).json()['city']['name']
                        flights.append({'city': city, 'price': firstPrice + secondPrice})
                    elif (firstPrice + secondPrice >= originalPrice):
                        break
                
                if (firstPrice + secondMinPrice >= originalPrice):
                    break
                
results = sorted(flights, key=lambda flight: flight['price'])       
print(results)

"""
outResults = results
inResults = [{'city': "Detriot", 'price': 100}, {'city': "Cleveland", 'price': 200}]
inPrice = 300
outPrice = 300
roundPrice = 290
routes = []
if outPrice + inPrice < roundPrice:
    for outRoute in outResults:
        for inRoute in inResults:
            routes.append({"cities":(outRoute['city'], inRoute['city']), "price": int(float(outRoute['price'])) + int(float(inRoute['price']))})
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
print(routes)
"""