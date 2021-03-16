from app import app
import geocoder, requests
from flask import jsonify, request
from error_handler import InvalidParams, InvalidResponse

GEOCODER_URL = "http://localhost:4000/v1/search"


@app.errorhandler(InvalidParams)
def handle_invalid_parameters(error):
    return error_response_builder(error, "INVALID_REQUEST")

def error_response_builder(error, status):
    response = jsonify({"status": status, "message": error.message})
    response.status_code = error.status_code
    return response


@app.route('/api/geocoder/<string:outputFormat>')
def geocode(outputFormat):
    # get our url parameters
    outputFormat = outputFormat.lower()
    address = request.args.get('address')

    # error handling
    if len(request.args) != 1:
        raise InvalidParams("Geocoder expects only one parameter (address)", 422)
    if not address or address == "":
        raise InvalidParams("Missing address parameter", 422)

    # collect our data
    geocoderUrl = GEOCODER_URL + "?text=" + address

    geocoderResponse = requests.get(geocoderUrl)

    if geocoderResponse.status_code != 200:
        raise InvalidResponse("Geocoder did not return ok", 503)

    geocoderJson = geocoderResponse.json()

    # build the response
    if(outputFormat == "json"):
        return buildGeocoderJson(address, geocoderJson)
    if(outputFormat == "xml"):
        return buildGeocoderXML(address, geocoderJson)
    raise InvalidParams("Invalid format. Use geocoder/json or geocoder/xml", 422)

def buildGeocoderJson(address, json):
    longitude = json['geocoding']['query']['focus.point.lat']
    latitude = json['geocoding']['query']['focus.point.lon']

    ret = {
        "results": [
            {
                "address_components": [
                    
                ],
                "formatted_address": address,
                "geometry": {
                    "location": {
                        "lat": latitude,
                        "lng": longitude
                    },
                    "viewport": {
                        "northeast": {
                            "lat": latitude + 0.02,
                            "lng": longitude + 0.02
                        },
                        "southwest": {
                            "lat": latitude - 0.02,
                            "lng": longitude - 0.02
                        }
                    }
                }
            }
        ],
        "status": "OK"
    }

    for key in json['geocoding']['query']['parsed_text']:
        if(key != 'subject'):
            insert = {
                "long_name": json['geocoding']['query']['parsed_text'][key],
                "short_name": json['geocoding']['query']['parsed_text'][key],
                "types": [key]
            }
            ret["results"][0]["address_components"].append(insert)

    return ret

def buildGeocoderXML(address, json):
    # set our data
    status = "OK"
    longitude = json['geocoding']['query']['focus.point.lat']
    latitude = json['geocoding']['query']['focus.point.lon']

    address_components = ""
    for key in json['geocoding']['query']['parsed_text']:
        if(key != 'subject'):
            part_type = key
            name = json['geocoding']['query']['parsed_text'][key]
            address_components += "<address_component><long_name>" + name + "</long_name><short_name>" + name + "</short_name><type>" + part_type + "</type></address_component>"
        
    # build the response
    ret = "<GeocodeResponse>" + \
        "<status>" + status + "</status>" + \
        "<result>" + \
            "<formatted_address>" + address + "</formatted_address>" + \
            address_components + \
            "<geometry>" + \
                "<location>" + \
                    "<lat>" + str(latitude) + "</lat><lng>" + str(longitude) +"</lng>" + \
                "</location>" + \
                "<viewport>" + \
                    "<southwest>" + \
                        "<lat>" + str(latitude + 0.02) + "</lat>" + \
                        "<lng>" + str(longitude + 0.02) + "</lng>" + \
                    "</southwest>" + \
                    "<northeast>" + \
                        "<lat>" + str(latitude - 0.02) + "</lat>" + \
                        "<lng>" + str(longitude - 0.02) + "</lng>" + \
                    "</northeast>" + \
                "</viewport>" + \
            "</geometry>" + \
        "</result>" + \
    "</GeocodeResponse>"
    return ret