# Import Dependencies
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, inspect
from sqlalchemy import func, and_
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, jsonify

# Create the connection engine
engine = create_engine("sqlite:///hawaii.sqlite", connect_args={'check_same_thread': False}, echo=True)

# Declare a Base using `automap_base()`
Base = automap_base()
# Use the Base class to reflect the database tables
Base.prepare(engine, reflect=True)
session = Session(bind=engine)
Base.classes.keys()

# Assign the measurements class to a variable called `Measurements`
Measurements = Base.classes.measurements
Stations = Base.classes.stations

#get distinct months in each year. use group by year and month in descending order
records = session.query(Measurements.date).group_by(func.strftime('%Y-%m', Measurements.date))\
        .order_by(Measurements.date.desc()).all()
records

# first record of list is start date and 12th record is the 12th month data
start_date = records[0]
end_date = records[12]

#use end date to select all data whose date is after the end date
prcp_records = session.query(Measurements.date, Measurements.prcp).filter(Measurements.date >= end_date[0]).all()
prcp_records

# save the list of tuples to a dataframe and set index as date
prcptn_df = pd.DataFrame.from_records(prcp_records)
prcptn_df = prcptn_df.rename(columns={0: 'Date', 1: 'Prcp'})
prcptn_df_12_mnts =prcptn_df.set_index('Date')
prcptn_df_12_mnts.head()


# create a plot
plt.style.use('ggplot')
prcptn_df_12_mnts.plot(figsize=(16,10), color="b")
#plt.savefig("Precipitation_Analysis.png")
#plt.show()

# query to get total number of stations
num_stations = session.query(func.count(Stations.id)).scalar()
num_stations

#query to get list of stations
list_stations = session.query(Stations.name).all()
list_stations = [station[0] for station in list_stations]

# get most active station. the station with highest number of observations is the most active station
stations_tobs = session.query(Measurements.station, func.count(Measurements.tobs)).group_by(Measurements.station).order_by\
(func.count(Measurements.tobs).desc()).all()
most_active_station = stations_tobs[0].station

#Filter by the station with the highest number of observations.

tobs_records = session.query(Measurements.station ,Measurements.date, Measurements.tobs).\
                filter(and_(Measurements.station == most_active_station, Measurements.date >= end_date[0]))\
                .order_by(Measurements.date.desc()).all()

# save the list of tuples to a dataframe
tobs_df = pd.DataFrame.from_records(tobs_records)
tobs_df = tobs_df.rename(columns={0: 'Station', 1: 'Date', 2:'Temp Observations'})
tobs_df.head()

#Plot the results as a histogram with bins=12.
tobs_df.hist(bins=12, color="royalblue")
plt.xlabel("")
plt.ylabel("Frequency")
plt.title("")
#plt.savefig("Station_Analysis.png")
#plt.show()

#Write a function called calc_temps that will accept a start date and end date in the format %Y-%m-%d and \
#return the minimum, average, and maximum temperatures for that range of dates.

def calc_temps(start_date, end_date):
    print("func start and end date", start_date, end_date)
    return session.query(func.min(Measurements.tobs), func.max(Measurements.tobs), func.avg(Measurements.tobs)).\
                filter(Measurements.date.between(start_date, end_date))\
                .all()
# Use the calc_temps function to calculate the min, avg, and max temperatures for your trip using the matching dates from the previous year
# (i.e. use "2017-01-01" if your trip start date was "2018-01-01")
temps = calc_temps("2017-02-23", "2017-02-28")
min_temp, max_temp, avg_temp = temps[0]

temps_df = pd.DataFrame.from_records(temps)
temps_df = temps_df.rename(columns={0: 'Min', 1: 'Max', 2:'Avg'})
temps_df

#Plot the min, avg, and max temperature from your previous query as a bar chart.
#Use the average temperature as the bar height.
#Use the peak-to-peak (tmax-tmin) value as the y error bar (yerr).

mean = temps_df['Avg']
errors = temps_df['Max'] - temps_df['Min']
fig, ax = plt.subplots()

mean.plot.bar(yerr=errors, ax=ax, width=0.5, figsize=(4,8), color="coral", alpha=0.7)
plt.xlabel("")
plt.ylabel("Temp(F)")
plt.title("Trip Avg Temp")
plt.xticks([])
#plt.savefig("Temperature_Analysis.png")
#plt.show()

# When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.
def calc_temp(start_date):
    results = session.query(func.min(Measurements.tobs), func.max(Measurements.tobs), func.avg(Measurements.tobs)).\
                filter(Measurements.date>=str(start_date)).all()

    temperature_list = list(np.ravel(results))
    return temperature_list




# Climate App

app = Flask(__name__)

@app.route("/")
def welcome():
    return ("<!DOCTYPE html><html><body>\
            <p>Available Routes:<p>\
            <p>/api/v1.0/precipitation</p> \
            <p>/api/v1.0/stations</p>\
            <p>/api/v1.0/tobs</p>\
            <p>/api/v1.0/&ltstart date&gt</p>\
            <p>/api/v1.0/&ltstart date&gt/&ltend date&gt</p>\
            </body></html>")

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the json representation of dates and precipitations from the last year, using date as the key and prcp as the value."""
    return jsonify(prcptn_df_12_mnts.to_dict())

@app.route("/api/v1.0/stations")
def stations():
    """Return a json list of stations from the dataset."""
    return jsonify(list_stations)

@app.route("/api/v1.0/tobs")
def temperature_observations():
    """Return a json list of Temperature Observations (tobs) for the previous year."""
    return jsonify(tobs_df['Temp Observations'].tolist())

@app.route("/api/v1.0/<start>")
def temperature_start_date(start):
    """Return a json list of the minimum temperature, the average temperature, and the max temperature for a given start range"""
    print(start)
    results = calc_temp(str(start))
    return jsonify(results)

@app.route("/api/v1.0/<start>/<end>")
def temperature_start_end_date(start, end):
    """Return a json list of the minimum temperature, the average temperature, and the max temperature for a given start-end range."""
    print("start date: ", start)
    print("end date: ", end)
    results = calc_temps(str(start), str(end))
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)