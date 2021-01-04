from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, make_response
import os
import json
import requests
import geocoder
import re
import populartimes
from operator import itemgetter, attrgetter
import pyrebase
from flask_cors import CORS

key = 'AIzaSyANqmnEgWqv-bZR0vXTQopHPPfiwWkkkqE'
config = {
    "apiKey" : 'AIzaSyAqEFmVsDH5PmYM2MGng6bLUJh5CHsS9pU',
    "authDomain" : "dinefind-e3e7c.firebaseapp.com",
    "databaseURL" : "https://dinefind-e3e7c.firebaseio.com",
    "storageBucket" : "dinefind-e3e7c.appspot.com"
}

firebase = pyrebase.initialize_app(config)  #Firebase object
db = firebase.database()                    #Firebase database object
auth = firebase.auth()                      #Firebase authentication object
storage = firebase.storage()                #Firebase storage object
app = Flask(__name__)
CORS(app)
def location():
    g = geocoder.ip('me')
    return "{}, {}".format(g.latlng[0], g.latlng[1])

def chain():
    f = open("chain.txt", "r")
    final = []
    for line in f:
        name = line.split("$")[0]
        name = name.split()
        name.pop(0)
        name = " ".join(name)
        name = name.lower()
        name = re.sub('\W+','', name)
        final.append(name)
    return final

def get_list(radius, location):
    URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    # location given here
    type = "restaurant"
    # defining a params dict for the parameters to be sent to the API
    PARAMS = {'location': location, 'radius': radius,'type': type, 'key': key}
    r = requests.get(url = URL, params = PARAMS)
    return r.json()

# fil = {open: 0, chain: 0, prev: 0, rating: 0}
def filter(data, fil):
    final = []
    if fil["open"] == 1:
        for index, place in enumerate(data["results"]):
            if place["opening_hours"]["open_now"] == True:
                if place not in final:
                    final.append(place)
    if fil["chain"] == 1:
        list_of_chain = chain()
        for index, place in enumerate(data["results"]):
            name = place["name"]
            name = name.lower()
            name = re.sub('\W+','', name)
            if name not in list_of_chain:
                if place not in final:
                    final.append(place)
    if fil["prev"] == 1:
        pass
    if fil["rating"] > 0:
        for index, place in enumerate(data["results"]):
            rating = place["rating"]
            if fil["rating"] <= rating:
                if place not in final:
                    final.append(place)
    flag = 0
    for key, val in fil.items():
        if val >= 1:
            flag = 1
            break

    if final == [] and flag == 0:
        final = data["results"]

    return final

# sor = {crowd: 0, price: 0, rating: 0}
# 0 does not sort, 1 is low to high, 2 is high to low
#[(a,b), (c,d)
def current_crowd(id):
    try:
        pop = populartimes.get_id(key, id)
        current = pop["current_popularity"]
    #popular_time = pop["populartimes"]
        return current
    except:
        return -1

def data_sort(data, sor):
    data_to_sort, asc_dsc, final, final_data, actual_val, nan_val = "", True, [], [], [], []
    for key, val in sor.items():
        if val == 1:
            data_to_sort = key
            asc_dsc = False
            break
        elif val == 2:
            data_to_sort = key
            asc_dsc = True
            break
    for index, place in enumerate(data["results"]):
        if key != "crowd":
            try:
                final.append((index, place[data_to_sort]))
            except:
                final.append((index, -1))
        else:
            id = place["place_id"]
            final.append((index, current_crowd(id)))
    sorted_array = sorted(final, key=itemgetter(1), reverse=asc_dsc)
    for index, item in enumerate(sorted_array):
        if item[1] == -1:
            nan_val.append(item)
        else:
            actual_val.append(item)
    actual_val += nan_val
    for item in actual_val:
        final_data.append(data["results"][int(item[0])])
    return final_data

@app.route("/")
def home():
    return render_template("index.html", var="hello")

@app.route("/data", methods=['POST', 'GET'])
def full():
    # data = get_list(15000, location())
    # filtered = filter(data, {"open": 0, "chain": 0, "prev": 0, "rating": 0})
    # new_data = {"results": filtered}
    # final = data_sort(new_data, {"crowd" : 0, "rating" : 1, "price_level" : 0})
    # out = json.dumps(final)
    # return render_template("index.html", var=out)
    if request.method == "POST":
        result = request.form
        radius = result["radius"]
        sor = json.loads(result["sor"])
        fil = json.loads(result["fil"])
        data = get_list(radius, location())
        filtered = filter(data, fil)
        new_data = {"results": filtered}
        final = data_sort(new_data, sor)
        out = json.dumps(final)
        return render_template("index.html", var=out)
    else:
        return redirect(url_for('home'))
# do not touch this! you fool hold your hands
# @app.route("/sort", methods=['POST', 'GET'])
# def sort_list():
#     if request.method == "POST":
#         result = request.form
#         radius = result["radius"]
#         sor = result["sor"]
#         data = get_list(radius, location())
#         final = data_sort(data, sor)
#         out = json.dumps(final)
#         return render_template("index.html", var=out)
#     else:
#         return redirect(url_for('home'))
#
#
# @app.route("/filter", methods=['POST', 'GET'])
# def filter_list():
#     if request.method == "POST":
#         result = request.form
#         radius = result["radius"]
#         fil = result["fil"]
#         data = get_list(radius, location())
#         final = data_sort(data, sor)
#         out = json.dumps(final)
#         return render_template("index.html", var=out)
#     else:
#         return redirect(url_for('home'))

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
