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


@app.route('/api/distancematrix/<string:outputFormat>')
def distance(outputFormat):
    # get our url parameters
    outputFormat = outputFormat.lower()
    origins = request.args.get('origins')
    destinations = request.args.get('destinations')

    # error handling
    if(not origins or origins == ""):
        raise InvalidParams("Parameter origins is required", 422)
    if(not destinations or destinations == ""):
        raise InvalidParams("Parameter destinations is required", 422)

    origins = origins.split("|")
    destinations = destinations.split("|") 

    locations = []
    for origin in origins:
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
            locationResponse = requests.get(locationPath)

            if locationResponse.status_code != 200:
                message = "Geocoder returned code " + str(locationResponse.status_code)
                raise InvalidResponse(message, 503)

            locationJson = locationResponse.json()

            if(not locationJson):
                raise InvalidResponse("Geocoder returned without a json", 503)

            temp = [locationJson["results"][0]["geometry"]["location"]["lng"], locationJson["results"][0]["geometry"]["location"]["lat"]]

        locationCoordinates.append([float(temp[0]), float(temp[1])])

    # build a request
    requestBody = {
        "locations": locationCoordinates,
        "metrics": ["duration", "distance"]
    }

    print("REQUEST BODY")
    print(requestBody)

    # collect our data
    distanceUrl = "http://localhost:8080/ors/v2/matrix/driving-car"
    distanceResponse = requests.post(distanceUrl, json=requestBody)

    # build the response
    if(outputFormat == "json"):
        return buildDistanceJson(origins, destinations, distanceResponse.json())
    if(outputFormat == "xml"):
        return buildDistanceXML(origins, destinations, distanceResponse.json())
    raise InvalidParams(
        "Invalid format. Use distancematrix/json or distancematrix/xml", 422)


def buildDistanceJson(origins, destinations, response):
    ret = {
        "status": "OK",
        "origin_addresses": origins,
        "destination_addresses": destinations,
        "rows": []
    }

    # only get the distances measured from the origin addresses
    for i in range(len(ret["origin_addresses"])):
        row = {"elements": []}
        for j in range(len(ret["destination_addresses"])):
            status = "OK"

            try:
                distance = response["distances"][i][i+j+1]
            except:
                distance = -1
                status = "NOT_FOUND"

            try:
                duration = response["durations"][i][i+j+1]
            except:
                duration = -1
                status = "NOT_FOUND"

            # check if our origin and destination are the same
            if(distance > 0):
                element = {
                            "distance": {
                                "text": distanceToString(distance),
                                "value": distance,
                            },
                            "duration": {
                                "text": durationToString(duration),
                                "value": duration,
                            },
                            "status": status
                        }
                row["elements"].append(element)
            else:
                row["elements"].append({"status": "NOT_FOUND"})
        ret["rows"].append(row)

    ret["response"] = response
    return ret


def buildDistanceXML(origins, destinations, response):
    
    # TODO pass an array of addresses to create this dynamically in a many to many scenario
    origin_addresses = "<origin_address>" + "TODO" + "</origin_address>"
    destination_addresses = "<destination_address>" + "TODO" + "</destination_address>"

    rows = "<row>"
    # dynamically create elements
    # TODO: dynamically set this range
    for index in range(1):

        status = "OK"

        try:
            distance = response["distances"][index][1]
        except:
            distance = -1
            status = "NOT_FOUND"

        try:
            duration = response["durations"][index][1]
        except:
            duration = -1
            status = "NOT_FOUND"

        rows += "<element>" + \
                    "<status>" + status + "</status>" + \
                    "<duration>" + \
                        "<value>" + str(duration) + "</value>" + \
                        "<text>" + durationToString(duration) + "</text>" + \
                    "</duration>" + \
                    "<distance>" + \
                        "<value>" + str(distance) + "</value>" + \
                        "<text>" + distanceToString(distance) + "</text>" + \
                    "</distance>" + \
                "</element>"
   
    rows += "</row>"

    ret = '<?xml version="1.0" encoding="UTF-8"?>' + \
        "<DistanceMatrixResponse>" + \
            "<status>" + status + "</status>" + \
            origin_addresses + destination_addresses + \
            rows + \
        "</DistanceMatrixResponse>"
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
