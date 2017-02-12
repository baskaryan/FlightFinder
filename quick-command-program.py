import os
import requests
from datetime import date, datetime


origin = "CLE"
destination = "SFO"
departDate = "2016-12-24"
returnDate = "2016-12-29"

if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")
key = os.environ.get("API_KEY")

control = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&return_date={}&number_of_results=1&apikey=4kLFYfEgqIjGCLli8wtsKYYOAZJG4QCg".format(origin, destination, departDate, returnDate))
originalPrice = int(float(control.json()['results'][0]['fare']['total_price']))

departD = date(int(departDate[:4]), int(departDate[5:7]), int(departDate[8:]))
returnD = date(int(returnDate[:4]), int(returnDate[5:7]), int(returnDate[8:]))
duration = (returnD - departD).days
firstList = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/inspiration-search?origin={}&departure_date={}&duration={}&max_price={}&apikey=4kLFYfEgqIjGCLli8wtsKYYOAZJG4QCg".format(origin, departDate, duration, int(originalPrice-75)))

flights = []
for flight in firstList.json()['results']:
    code = flight['destination']
    firstMinPrice = int(float(flight['price']))
    second = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&return_date={}&max_price={}&apikey=4kLFYfEgqIjGCLli8wtsKYYOAZJG4QCg".format(code, destination, departDate, returnDate, originalPrice-firstMinPrice))
    found = False
    
    if second.status_code == 200:
        secondFlight = second.json()
        secondMinPrice = int(float(secondFlight['results'][0]['fare']['total_price']))
        first = requests.get("http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={}&destination={}&departure_date={}&return_date={}&max_price={}&apikey=4kLFYfEgqIjGCLli8wtsKYYOAZJG4QCg".format(origin, code, departDate, returnDate, originalPrice-secondMinPrice))
        
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
                        city = requests.get("http://api.sandbox.amadeus.com/v1.2/location/{}/?apikey=4kLFYfEgqIjGCLli8wtsKYYOAZJG4QCg".format(code)).json()['city']['name']
                        flights.append({'city': city, 'price': firstPrice + secondPrice})

                    elif (firstPrice + secondPrice >= originalPrice):
                        break
                
                if (firstPrice + secondMinPrice >= originalPrice):
                    break

    
results = sorted(flights, key=lambda flight: flight['price'])       
print(results)
