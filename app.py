from flask import Flask, redirect, render_template, request, jsonify
# import pandas as pd
from config import conn
from flask_sqlalchemy import SQLAlchemy
import pymysql
pymysql.install_as_MySQLdb()
from sqlalchemy.ext.automap import automap_base
import simplejson as json

# Set up flask and db
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{conn}/eatinerary'
db=SQLAlchemy(app)
Base=automap_base()
Base.prepare(db.engine, reflect = True)

# Prepping both tables
restaurant=Base.classes.restaurant
category=Base.classes.category

# Home route
@app.route("/")
def home():
    return render_template("index.html")

####################################
# API route to query restaurant data
####################################
@app.route("/api/<city>/<clientTime>/<attributes>", methods = ['GET'])
def data(city='', clientTime='0', attributes=[]):

    # Convert the variables passed from JSON stringify
    clientTime = json.loads(clientTime)
    attributes = json.loads(attributes)

    # Print the avariables received in console
    print(f'City: {city}')

    # Convert the day to a string and print the value
    if clientTime['day'] == 0:
        day = 'Sunday'
        print(f"Day: {day}")

    elif clientTime['day'] == 1:
        day = 'Monday'
        print(f"Day: {day}")

    elif clientTime['day'] == 2:
        day = 'Tuesday'
        print(f"Day: {day}")

    elif clientTime['day'] == 3:
        day = 'Wednesday'
        print(f"Day: {day}")
        
    elif clientTime['day'] == 4:
        day = 'Thursday'
        print(f"Day: {day}")

    elif clientTime['day'] == 5:
        day = 'Friday'
        print(f"Day: {day}")
        
    elif clientTime['day'] == 6:
        day = 'Saturday'
        print(f"Day: {day}")

    print(f"Time: {clientTime['h']}:{clientTime['m']}")

    # Convert clientTime to minutes
    clientTimeM = clientTime['h']*60 + clientTime['m']
    print(f'Time in minutes: {clientTimeM}')

    # Select statement for all the desired columns
    sel_category = [
        category.Category_id,
        category.Category
    ]

    # Construct the query
    query_category = db.session.query(*sel_category)

    # Convert the list of queries to a dictionary with the key as the
    # category and the value as the category name this will be used
    # later to convert the comma separated category ids to a list of
    # categories
    category_dict = {row[0] : row[1] for row in query_category.all()}

    # Select statement for all the desired columns
    sel_restaurant = [
        restaurant.Name,
        restaurant.Address,
        restaurant.Postal_code,
        restaurant.City,
        restaurant.Latitude,
        restaurant.Longitude,
        restaurant.Stars,
        restaurant.Monday_open,
        restaurant.Monday_close,
        restaurant.Tuesday_open,
        restaurant.Tuesday_close,
        restaurant.Wednesday_open,
        restaurant.Wednesday_close,
        restaurant.Thursday_open,
        restaurant.Thursday_close,
        restaurant.Friday_open,
        restaurant.Friday_close,
        restaurant.Saturday_open,
        restaurant.Saturday_close,
        restaurant.Sunday_open,
        restaurant.Sunday_close,
        restaurant.Category_ids
    ]

    # Construct the initial query
    query_restaurant = db.session.query(*sel_restaurant) \
        .filter(restaurant.City == city)


    for attribute in attributes:
        if attribute['name'] == 'OpenNow':
            # If the row represents the openNow checkbox
            if attribute['value'] == True:
                # If the user only wants restaurants that are currently open
                #
                # Check that the client time is within the closing and
                # opening time that the restaurant has listed for today
                # and add it to the query
                query_restaurant = query_restaurant \
                    .filter(getattr(restaurant, f'{day}_open') \
                        <= clientTimeM) \
                    .filter(getattr(restaurant, f'{day}_close') \
                        >= clientTimeM)
        else:
            if attribute['value'] == True:
                # If the user checked the checkbox get the column name from
                # the name key and only select restaurants that have a true
                #  value in that column
                column = attribute['name']
                print(f'{column}: true')
                query_restaurant = query_restaurant \
                    .filter(getattr(restaurant,column) == True)

    print(f'# of responses: {len(query_restaurant.all())}')

    # Empty list to append results from the restaurant table to
    map_data = []
    latitudes = []
    longitudes = []
    latitude_avg = 0
    longitude_avg = 0

    if len(query_restaurant.all()) == 0:
        # If there are no results return 204 no content error
        return jsonify(
            map_data=map_data,
            latitude_avg=latitude_avg,
            longitude_avg=longitude_avg
            ) 

    else:

        # Return the results found
        for row in query_restaurant.all():

            # Split the category ids on comma then replace each with
            # corresponding category from the dictionary of categories
            category_ids = row[21].split(',')
            categories = [category_dict.get(int(value)) for value in category_ids]

            # Append each row in the result as a dictionary
            map_data.append({
                'Name': row[0],
                'Address': row[1],
                # 'Postal_code': row[2],
                # 'City': row[3],
                'Latitude': row[4],
                'Longitude': row[5],
                'Stars': row[6],
                # 'Monday_open': row[7],
                # 'Monday_close': row[8],
                # 'Tuesday_open': row[9],
                # 'Tuesday_close': row[10],
                # 'Wednesday_open': row[11],
                # 'Wednesday_close': row[12],
                # 'Thursday_open': row[13],
                # 'Thursday_close': row[14],
                # 'Friday_open': row[15],
                # 'Friday_close': row[16],
                # 'Saturday_open': row[17],
                # 'Saturday_close': row[18],
                # 'Sunday_open': row[19],
                # 'Sunday_close': row[20],
                'Categories': categories
            })

            latitudes.append(row[4])
            longitudes.append(row[5])

        # Calculating the center of the map for map.js
        latitude_avg = (max(latitudes) + min(latitudes))/2
        longitude_avg = (max(longitudes) + min(longitudes))/2
        print(f'Lat: {latitude_avg}')
        print(f'Long: {longitude_avg}')

        # Return two JSON separate objects
        return jsonify(
            map_data=map_data,
            latitude_avg=latitude_avg,
            longitude_avg=longitude_avg
            ) 

#############################################
# API route to return a json of unique cities
#############################################
@app.route("/api/cityList", methods=['GET'])
def cityList():

    # Empty list to store the results in
    results = []

    # Query for all the unique cities
    query=db.session.query(restaurant.City).distinct(restaurant.City)

    # Append results to the empty list
    for row in query.all():
        results.append(row[0])

    # Return the results as JSON
    return jsonify(results)

############################################
# Route to display information about the app
############################################
@app.route("/about")
def about():
   return render_template("about.html")

###########################
# Contact information route
###########################
@app.route("/contact")
def contact():
   return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)