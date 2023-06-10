import io
import os
import shutil
import zipfile
import pandas as pd
import sys

TRIPS_ROWS_LIMIT = int(sys.argv[1])

print("Generating datasets with {} rows (each city)".format(TRIPS_ROWS_LIMIT))

try:
    shutil.rmtree("./output")
except:
    pass
import os

os.mkdir("./output")
os.mkdir("./output/montreal")
os.mkdir("./output/toronto")
os.mkdir("./output/washington")

zip_file = zipfile.ZipFile("./full_data.zip")
csv_files = [file for file in zip_file.namelist() if file.endswith(".csv")]
for csv in csv_files:
    city = csv.split("/")[0]
    data = csv.split("/")[1].rstrip(".csv")
    with zip_file.open(csv) as csv_file:
        print(f"Processing: {city} {data}")
        if data == "station":
            stations = pd.read_csv(io.TextIOWrapper(csv_file), delimiter=",")
            stations.to_csv(f"./output/{city}/stations.csv", index=False)
        if data == "trip":
            trips = pd.read_csv(
                io.TextIOWrapper(csv_file), delimiter=",", nrows=TRIPS_ROWS_LIMIT
            )
            trips.to_csv(f"./output/{city}/trips.csv", index=False)
        if data == "weather":
            weather = pd.read_csv(io.TextIOWrapper(csv_file), delimiter=",")
            weather.to_csv(f"./output/{city}/weather.csv", index=False)

import os
from collections import defaultdict

import numpy as np
import pandas as pd

TRIPS_ROWS_LIMIT = 1000000
TYPE_TRIPS = "trips"
TYPE_STATIONS = "stations"
TYPE_WEATHER = "weather"

cities = set()
paths_by_city_and_type = defaultdict(dict)
for dirname, _, filenames in os.walk("./output"):
    for filename in filenames:
        city = os.path.basename(dirname)
        cities.add(city)
        file_type = os.path.splitext(filename)[0]
        paths_by_city_and_type[city][file_type] = os.path.join(dirname, filename)

# print(cities)
# print(paths_by_city_and_type)

import datetime

weather_by_city = {}
for city in cities:
    weather = pd.read_csv(paths_by_city_and_type[city][TYPE_WEATHER], delimiter=",")
    weather = weather[["date", "prectot"]]
    weather["date"] = pd.to_datetime(weather["date"]).apply(
        lambda t: (t - datetime.timedelta(days=1)).date()
    )
    weather_by_city[city] = weather

stations_by_city = {}
for city in cities:
    stations = pd.read_csv(paths_by_city_and_type[city][TYPE_STATIONS], delimiter=",")
    stations_by_city[city] = stations

trips_list = []
for city in cities:
    city_trips = pd.read_csv(
        paths_by_city_and_type[city][TYPE_TRIPS], delimiter=",", nrows=TRIPS_ROWS_LIMIT
    )
    city_trips.loc[city_trips["duration_sec"] < 0, "duration_sec"] = 0
    city_trips["start_date"] = pd.to_datetime(city_trips["start_date"])
    city_trips["end_date"] = pd.to_datetime(city_trips["end_date"])
    city_trips["start_date_day"] = city_trips["start_date"].apply(lambda t: t.date())
    city_trips = city_trips.merge(
        weather_by_city[city], left_on="start_date_day", right_on="date"
    )
    city_trips = city_trips.merge(
        stations_by_city[city],
        left_on=["start_station_code", "yearid"],
        right_on=["code", "yearid"],
    )
    city_trips.rename(
        columns={
            "name": "start_station_name",
            "latitude": "start_station_latitude",
            "longitude": "start_station_longitude",
        },
        inplace=True,
    )
    city_trips = city_trips.merge(
        stations_by_city[city],
        left_on=["end_station_code", "yearid"],
        right_on=["code", "yearid"],
    )
    city_trips.rename(
        columns={
            "name": "end_station_name",
            "latitude": "end_station_latitude",
            "longitude": "end_station_longitude",
        },
        inplace=True,
    )
    city_trips["city"] = city
    city_trips = city_trips.drop(
        columns=[
            "start_date",
            "start_station_code",
            "end_date",
            "end_station_code",
            "is_member",
            "code_x",
            "code_y",
            "date",
        ]
    )
    trips_list.append(city_trips)

trips = pd.concat(trips_list)
trips_list = None

# Query 1 - Average duration on trips during >20mm precipitation days
print("#################### RAINY QUERY ####################")
print(trips[trips.prectot > 30].groupby(["start_date_day"])["duration_sec"].mean())

# Query 2 -
print("#################### 2016_2017 query ####################")
station_trips_totals = (
    trips.groupby(["start_station_name", "yearid"]).size().reset_index(name="qty_trips")
)
station_trips_2016 = station_trips_totals[station_trips_totals.yearid == 2016][
    ["start_station_name", "qty_trips"]
]
station_trips_2017 = station_trips_totals[station_trips_totals.yearid == 2017][
    ["start_station_name", "qty_trips"]
]
station_trips = station_trips_2017.merge(
    station_trips_2016,
    left_on="start_station_name",
    right_on="start_station_name",
    suffixes=("_qty_2017", "_qty_2016"),
)
print(
    station_trips[
        station_trips.qty_trips_qty_2017 > 2 * station_trips.qty_trips_qty_2016
    ]
)

# Query 3 - Stations with more than 6km avg to arrive at them
print("#################### MONTREAL query ####################")
from haversine import haversine

montreal_trips = trips[trips.city == "montreal"]
trips = None
station_distances_array = montreal_trips.apply(
    lambda r: [
        r["end_station_name"],
        haversine(
            (r["start_station_latitude"], r["start_station_longitude"]),
            (r["end_station_latitude"], r["end_station_longitude"]),
        ),
    ],
    axis=1,
)
montreal_trips = None
station_distances = pd.DataFrame(
    station_distances_array.values.tolist(), columns=["end_station_name", "distance"]
)
montreal_station_mean_distances = (
    station_distances.groupby(["end_station_name"])["distance"].mean().reset_index()
)
print(montreal_station_mean_distances[montreal_station_mean_distances.distance >= 6])


print("#################### GENERATING data.zip ####################")
import os
import zipfile

zip_file = zipfile.ZipFile("./data.zip", "w", zipfile.ZIP_DEFLATED)
zip_file.write("./output/montreal/trips.csv", "/montreal/trips.csv")
zip_file.write("./output/montreal/stations.csv", "/montreal/stations.csv")
zip_file.write("./output/montreal/weather.csv", "/montreal/weather.csv")

zip_file.write("./output/toronto/trips.csv", "/toronto/trips.csv")
zip_file.write("./output/toronto/stations.csv", "/toronto/stations.csv")
zip_file.write("./output/toronto/weather.csv", "/toronto/weather.csv")

zip_file.write("./output/washington/trips.csv", "/washington/trips.csv")
zip_file.write("./output/washington/stations.csv", "/washington/stations.csv")
zip_file.write("./output/washington/weather.csv", "/washington/weather.csv")

print("#################### CLEANING WORKSPACE ####################")
shutil.rmtree("./output")
