#!/usr/bin/env python
import googlemaps
import gmplot
import csv
import sys
import itertools
import math
import copy
import webbrowser, os

from datetime import datetime

import cgi
import cgitb

print ("Content-type:text/html\r\n\r")

""" DEFINITIONS """
WEBPAGE_NAME    = "gerts.html"
FROM_LOCATION   = "New Museum, 235 Bowery, New York, NY 10002, USA"
TO_LOCATION     = "Times Square, Manhattan, NY 10036, USA"
API_KEY 	    = "AIzaSyC5r9BMxuBBonbAo8Cty4GR3Vs9v_4MQeQ"
COLLISIONS_FILE = "collisions.txt"
NYC_COLLISIONS_FILE = "NYC-vehicle-collisions.csv"
SAFE_COLOR = '#009933'
UNSAFE_COLOR = '#ff0000'

topLeftLat = 41.158546
topLeftLon = -74.524643
squareSize = 0.001



# Get gmaps api
gmaps = googlemaps.Client(key=API_KEY)


collisions = []

#print "parsing collisions.."
with open(COLLISIONS_FILE) as textFile: 

	 for line in textFile:

	 	inRow = False

	 	row = []

	 	for i in range(1, len(line)-1):

	 		if (line[i] == "," or line[i] == "[" or line[i] == " "):
	 			continue

	 		if (line[i] == "]"):
	 			collisions.append(row)
	 			row = []
	 			continue

	 		row.append(int(line[i]))


#print "completed parsing collisions.."


def interp(lat1, lng1, lat2, lng2, count, lat_list, lng_list):

	if (count <= 0):
		return 1

	lat_mid_temp = (lat1 + lat2) / 2.0
	lng_mid_temp = (lng1 + lng2) / 2.0

	temp = (lat_mid_temp, lng_mid_temp)

	results = gmaps.snap_to_roads(temp, interpolate=False)
	result = results[0]

	location = result['location']
	lat_mid = location['latitude'];
	lng_mid = location['longitude'];

	count -= 1;

	val = 0

	val += interp(lat1, lng1, lat_mid, lng_mid, count, lat_list, lng_list);

	lat_list.append(lat_mid);
	lng_list.append(lng_mid);

	val += interp(lat_mid, lng_mid, lat2, lng2, count, lat_list, lng_list);

	return val

def interpolate(steps):

	paths = []

	latitudes = []
	longitudes = []

	original_latitudes = []
	original_longitudes = []

	latitudes_final = []
	longitudes_final = []

	# loop each waypoint
	for step in steps:

		start_location = step['start_location']
		lat_start = start_location['lat'];
		lng_start = start_location['lng'];

		latitudes.append(lat_start);
		longitudes.append(lng_start);

	original_latitudes = copy.copy(latitudes)
	original_longitudes = copy.copy(longitudes)


	max_interp_metric = 3
	length = len(latitudes)
	num_nodes = length

	for i, j in zip(range(length), range(1, length)):

		lat1 = latitudes[i]
		lng1 = longitudes[i]

		lat2 = latitudes[j]
		lng2 = longitudes[j]

		dist = math.sqrt(abs(lat1 - lat2) ** 2  + abs(lng1 - lng2) ** 2)
#		print dist

		"""
		metric = int(dist / 0.0005)
#		print metric

		if (metric <= 0):
			metric = 1

		elif (metric > max_interp_metric):
			metric = max_interp_metric

		metric = 0
		"""
		latitudes_final.append(lat1)
		longitudes_final.append(lng1)

		num_nodes += interp(lat1, lng1, lat2, lng2, max_interp_metric, latitudes_final, longitudes_final)

		latitudes_final.append(lat2)
		longitudes_final.append(lng2)



	return (latitudes_final, longitudes_final, original_latitudes, original_longitudes, num_nodes)




def findLatLonIndex(latitude, longitude):
    latIndex = int(math.fabs(topLeftLat - latitude)/squareSize)
    lonIndex = int(math.fabs(topLeftLon - longitude)/squareSize)
    latlonIndex = (latIndex, lonIndex)
    return latlonIndex


def calculateScore(latitudes,longitudes, num_nodes):

	score = 0

	for i in range(len(latitudes)):

		lat = latitudes[i]
		lng = longitudes[i]

		ind = findLatLonIndex(lat, lng)

		lat_ind = ind[0]
		lng_ind = ind[1]

		score += collisions[lat_ind][lng_ind]

	score/= (num_nodes * 1.0)

	return score

def getDataPoints(num):

	latitudes = []
	longitudes = []

	count = 0
	with open(NYC_COLLISIONS_FILE, 'rb') as csvfile:
		reader = csv.reader(csvfile)

		for row in reader:

			try:
				lat = float(row[5])
				lon = float(row[6])
			except: 
				continue;

			if (lat == 0.0 or lon == 0.0):
				continue;

			latitudes.append(lat)
			longitudes.append(lon)

			count+=1;

			#if (count > num):
			#	break;

	return (latitudes, longitudes)

form = cgi.FieldStorage()


""" FORM SETTINGS """
from_location = form['origin'].value
to_location   = form['destination'].value
""""""

paths = []
routes  = gmaps.directions(from_location, to_location, alternatives=True)
#print len(routes)

# get each calculated route
count = 0
min_score = -1
optimal_route = 0
for route in routes:

#	print "interpolating route ", count, "..."

	legs = route['legs']
	leg = legs[0]

	steps = leg['steps']

	result = interpolate(steps)

	latitudes = result[0]
	longitudes = result[1]
	num_nodes = result[4]

#	print "completed interpolating route ", count, "..."
#	print "number of nodes: ", num_nodes

#	print "finding score of route ", count, "..."

	score = calculateScore(latitudes, longitudes, num_nodes)

#	print "route ", count, " score: ", score

	if (min_score == -1 or score < min_score):
		min_score = score
		optimal_route = count

	paths.append(result)

	count+=1



#print "grabbing nyc data..."
result = getDataPoints(1000)
#print "completed grabbing nyc data..."

data_lat = result[0]
data_lng = result[1]


gmap = gmplot.GoogleMapPlotter.from_geocode("New York City")


safe = "green"
unsafe = "red"

for i in range(len(paths)):

	path = paths[i]

	latitudes = path[0]
	longitudes = path[1]

	original_latitudes = path[2]
	original_longitudes = path[3]

	color = UNSAFE_COLOR
	c = unsafe

	if (i == optimal_route):
		color = SAFE_COLOR
		c = safe

	
	gmap.scatter(latitudes, longitudes, color, size=20, marker=False)


	gmap.plot(latitudes, longitudes, c, edge_width=10)


gmap.heatmap(data_lat, data_lng)


gmap.draw(WEBPAGE_NAME)

#print "Content-type: text/html"
#print "<!doctype HTML>"
#print
#with open('gerts.html') as f:
 # print f.read()

#f.close()

webbrowser.open('file://' + os.path.realpath(WEBPAGE_NAME), new=2)




