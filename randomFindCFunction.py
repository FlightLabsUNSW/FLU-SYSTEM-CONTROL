import numpy as np
import math
import json
import argparse

# Importing the Data from the .json file
open('mission_data.json','r') as data_f:
	mission_data = json.load(data_f)

waypointType = 16
default_alt = 150.000000
header_name = "QGC WPL 110"

# ArgParse Default Values
stepDistanceMin = 10.0 # in kilometers
exclusionRadiusToleranceMin = 10.0 # in kilometers

# Parser Arguments
parse = argparse.ArgumentParser(description = "Constructs a Flight Path from Given Waypoints and Obstacles")
parser.add_argument("json_file", help = 'Input Mission Data .JSON File')
parser.add_argument("--step", action = "store", dest = "stepDistance", type = float, default = stepDistanceMin, help = "Step Distance between Target Point - Define in km")
parser.add_argument("--tolerance", action = "store", dest = "exclusionRadiusTolerance", type = float, default = exclusionRadiusToleranceMin, help = "Tolerance for Exclusion Radius around Obstacles - Define in km")

results = parser.parse_args()
mission_data = results.json_file
stepDistance = results.stepDistance
exclusionRadiusTolerance = results.exclusionRadiusTolerance

# Import Waypoint and Obstacle Data from Mission Data
def extractMissionData(mission_data):
	### INPUTS ###
	# mission_data - dictionary - Received Mission Data
	### OUTPUTS ###
	# waypoints - list - List of Coordinate Vectors for Waypoints
	# exclusionPoints - list - List of Coordinate Vectors for Obstacles
	# exclusionRadius - list - List of Exclusion Radii around Obstacles

	# Extract the Latitude and Longitude from each Waypoint
	for waypoint in mission_data["waypoints"]:
		waypoints.append(np.array([waypoint["latitude"], waypoint["longitude"]]))

	# Extract the Latitude, Longitude and Radius from each Obstacle
	for obstacle in mission_data["stationaryObstacles"]:
		exclusionPoints.append(np.array([ obstacle["latitude"], obstacle["longitude"] ]))
		exclusionRadius.append(obstacle["radius"])

	return (waypoints, exclusionPoints, exclusionRadius)

### NOTE ###
# Coordinates of All Points should be given as:
# Latitude - Considered x Coordinates
# Longitude - Considered y Coordinates

# Determine Distance between Two Points (Also the Haversine Function!)
def distanceTwoPoints(firstPoint, secondPoint):
	### INPUTS ###
    # firstPoint - 2x1 numpy.array - coordinate Vector to First Point
    # secondPoint - 2x1 numpy.array - Coordinate Vector to Second Point
	### OUTPUT ###
	# distance - Float - Distance between Two Points

	R = 6372.795477598 # Radius of Earth in km

	distance = R * arcmath.cos( math.sin(firstPoint[0]) * math.sin(secondPoint[0]) + math.cos(firstPoint[0]) * math.cos(secondPoint[0]) * math.cos(firstPoint[1]) - secondPoint[1]))

	return distance

# Obtains Position of Third Point given Two Points and Distance between First and Third
def extendVecByDist(firstPoint, secondPoint, distance):
    ### INPUTS ###
    # firstPoint - 2x1 numpy.array - Coordinate Vector to First Point
    # secondPoint - 2x1 numpy.array - Coordinate Vector to Second Point
    # distance - float - Distance between First Point and Third Point
    ### OUTPUT ===
    # thirdPoint - 2x1 numpy.array - Coordinate Vector to Third Point

	# Mathematically Define Position of Third Point
    thirdPoint = firstPoint + distance/distanceTwoPoints(firstPoint, secondPoint)*(secondPoint - firstPoint)

    return thirdPoint

# Calculates the Angular Bearing between Two Points
def calculateBearing(firstPoint, secondPoint):
    ### INPUTS ###
    # firstPoint - 2x1 numpy.array - Coordinate Vector to First Point
    # secondPoint - 2x1 numpy.array - Coordinate Vector to Second Point
    ### OUTPUT ###
    # theta - float - Bearing Angle in Radians

	# Determine change in latitude and longitude
    delta_Lat = math.log( math.tan( secondPoint[0]/2 + pi/4 )/math.tan( firstPoint[0]/2 + pi/4) )
    delta_Long = abs(firstPoint[1]] - secondPoint[1])

	# Keep the change in longitude within the domain of -180 < delta_Long < 180
    if delta_Long > 180:
        delta_Long = delta_Long % 180

	# Calculate bearing angle
    bearing = math.atan2(delta_Long, delta_Lat)

    return bearing

# Obtains Second Point given Distance and Bearing from First Point
def pointFromDistBear(firstPoint, thirdPoint, distance):
    ### INPUTS ###
    # firstPoint - 2x1 numpy.array - coordinate Vector to First Point
    # secondPoint - 2x1 numpy.array - Coordinate Vector to Second Point
    # distance - Float - Distance from First to Second Point
    ### OUTPUT ###
    # secondPoint - 2x1 numpy.array - Coordinate Vector to Second Point

    # Calculations: https://www.sunearthtools.com/tools/distance.php

    R = 6372.795477598 # Radius of Earth in km

	# Calculate bearing angle
    bearing = calculateBearing(firstPoint, thirdPoint)

	# Determine Position of Second Point
    lat2 = amath.sin( math.sin(firstPoint[0]) * math.cos(distance/R) + math.cos(firstPoint[0]) * math.sin(distance/R) * math.cos(bearing) )
    long2 = firstPoint[1] + math.atan2( math.sin(bearing) * math.sin(distance/R) * math.cos(firstPoint[0]), math.cos(distance/R) - math.sin(firstPoint[0]) * math.sin(lat2))

    secondPoint = [lat2, long2]

    return secondPoint

# ===== Main Function =====
#Determine Flight Path with Given Waypoints and Target Points
def calculateFlightPath(waypoints, exclusionPoints, stepDistance, exclusionRadius):
	### INPUTS ###
	# waypoints - nx1 numpy.array - List of Waypoint Coordinate Vectors
	# exclusionPoints - nx1 numpy.array - List of Centres for Exclusion Zones
	# stepDistance - float - Incremental Distance between Consecutive Target Points
	# exclusionRadius - float - Radius of Exclusion Zones to be Considered
	### Output ###
	# flightPath - nx1 numpy.array - List of Target Point Coordinate Vectors Tracing Flight Path

	if len(waypoints) < 2:
		print("There are not enough waypoints provided!")
		return None

	# For each pair of waypoints...
	for i in range(len(waypoints) - 1):
		flightPath.append(waypoints[i])
		# 1. Determine list of target points between two waypoints at set incremental distance
		# 1a. Find distance between two waypoints
		totalDistance = distanceTwoPoints(waypoints[i], waypoints[i+1])

		# 1b. Calculate total number of target points between two waypoints
		numPoints = math.floor(totalDistance / stepDistance)

		# 1c. Locate target points at incremental distances
		targetPoints = []
		for j in range(numPoints):
			targetPoint = pointFromDistBear( waypoints[i], waypoints[i+1], stepDistance * (j+1))

			# 2. Shift target points if within exclusion radius
			exclusionDistance = []
			# 2a. For each target point, evaluate distance to all exclusion points
			for k in range(len(exclusionPoints)):
				exclusionDistance = distanceTwoPoints(targetPoint, exclusionPoints[k])
			# 2b. Identify the closest distance
			# 2c. If distance is less than exclusion radius, shift target point to outside of it
			if min(exclusionDistance) < exclusionRadius[k]:
				minIndex = exclusionDistance.index(min(exclusionDistance))
				targetPoint = extendVecByDist(exclusionPoints[minIndex], targetPoint, exclusionRadius[k])
			flightPath.append(targetPoint)
			# 2d. Iterate for the other target points

	flightPath.append(waypoints[-1])

    # 3. If three consecutive waypoints are collinear, remove the middle waypoint.
    for index, point in enumerate(flightPath[1:-1]):
        bearing1 = calculateBearing( flightPath[index-1], point)
        bearing2 = calculateBearing( point, flightPath[index + 1])
        if bearing1 == bearing2:
            flightPath.remove(point)

	return flightPath

def exportMission(waypointType, flightPath, default_alt):
    ### INPUTS ###
    # waypointType - integer - Number defining Waypoint Type
    # flightPath - nx1 list - List storing Coordinate Vectors for Travel Points for Flight
    # default_alt - float - Default Altitude
    ### OUTPUT ###
    # mpmission.waypoint - waypoint file - Waypoint File for Mission Planner

    file = open("mpmission.waypoint","w")

    file.write(header_name + "\n")
    for idx, point in enumerate(flightPath):
        file.write( str(idx) + "\t0\t0\t" + str(waypointType) + "\t0.000000\t0.000000\t0.000000\t0.000000\t" +
            "{:.6f}".format(point[0]) + "\t" + "{:.6f}".format(point[1]) + "\t" + "{:.6f}".format(default_alt) +
            "\t" + str(1) + "\n")
