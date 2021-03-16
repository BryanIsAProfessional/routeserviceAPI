from app import app
import requests
from flask import jsonify, request
from error_handler import InvalidParams, InvalidResponse


@app.errorhandler(InvalidParams)
def handle_invalid_parameters(error):
    return error_response_builder(error, "INVALID_REQUEST")


def error_response_builder(error, status):
    response = jsonify({"status": status, "message": error.message})
    response.status_code = error.status_code
    return response


@app.route('/api/directions/<string:outputFormat>')
def directions(outputFormat):
    # get our url parameters
    outputFormat = outputFormat.lower()
    origin = request.args.get('origin')
    destinations = request.args.get('destination')

    # error handling
    if(not origin or origin == ""):
        raise InvalidParams("Parameter origins is required", 422)
    if(not destinations or destinations == ""):
        raise InvalidParams("Parameter destinations is required", 422)

    destinations = destinations.split("|") 

    locations = []
    locations.append(origin)

    for destination in destinations:
        locations.append(destination)

    locationCoordinates = []
    # convert our locations to coordinates if they aren't already
    # then add them to our request body
    for location in locations:
        # check if our origin is already in [lat,lng] format
        temp = location.split(',')
        if(not (len(temp) == 2 and isinstance(temp, float))):
            locationPath = "http://127.0.0.1:5000/api/geocoder/json?address=" + location

            print(locationPath)

            locationResponse = requests.get(locationPath)

            if locationResponse.status_code != 200:
                message = "Geocoder returned code " + str(locationResponse.status_code)
                raise InvalidResponse(message, 503)

            locationJson = locationResponse.json()

            if(not locationJson):
                raise InvalidResponse("Geocoder returned without a json", 503)

            temp = [locationJson["results"][0]["geometry"]["location"]["lng"], locationJson["results"][0]["geometry"]["location"]["lat"]]

        locationCoordinates.append([float(temp[0]), float(temp[1])])

    # collect our data
    distanceUrl = "http://localhost:8080/ors/v2/directions/driving-car"
    
    requestBody = {
        "coordinates": locationCoordinates
    }

    distanceResponse = requests.post(distanceUrl, json=requestBody)

    if(outputFormat == "json"):
        return buildDirectionsJson(origin, destinations, locationCoordinates, distanceResponse.json())
    return {"message": "Format is invalid."}


def buildDirectionsJson(originAddress, destinationAddresses, locationCoordinates, response):

    return response

    ret = {
        "geocoded_waypoints": [
          {
              "geocoder_status": "OK",
          },
            {
              "geocoder_status": "OK",
              "partial_match": True,
              "types": ["route"]
          }
        ],
        "routes": [
            {
                "bounds": {
                    "northeast": {
                        "lat": "TODO",
                        "lng": "TODO"
                    },
                    "southwest": {
                        "lat": "TODO",
                        "lng": "TODO"
                    }
                },
                "legs": [
                    {
                        "distance": {
                            "text": distanceToString(response["features"][0]["properties"]["summary"]["distance"]),
                            "value": response["features"][0]["properties"]["summary"]["distance"]
                        },
                        "duration": {
                            "text": durationToString(response["features"][0]["properties"]["summary"]["duration"]),
                            "value": response["features"][0]["properties"]["summary"]["duration"]
                        },
                        "end_address": destinationAddresses[0],
                        "end_location": {
                            "lat": locationCoordinates[0][1],
                            "lng": locationCoordinates[0][0]
                        },
                        "start_address": originAddress,
                        "start_location": {
                            "lat": locationCoordinates[0][1],
                            "lng": locationCoordinates[0][0]
                        },
                    }
                ],
                "warnings": [],
                "waypoint_order": []
            }
        ],
        "status": "OK"
    }
    return ret

def distanceToString(meters):
    # truncate to 1 decimal place
    km = int((meters/1000) * 10) / 10
    ret = str(km) + " km"
    return ret


def durationToString(seconds):
    ret = ""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if(hours > 0):
        ret = str(int(hours)) + " hours"
    if(seconds > 30):
        minutes += 1
    ret += str(int(minutes)) + " minutes"
    return ret