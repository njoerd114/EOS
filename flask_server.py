#!/usr/bin/env python3
from flask import Flask, jsonify, request, redirect, url_for
import numpy as np
from  modules.class_load import *
from  modules.class_ems import *
from  modules.class_pv_forecast import *
from modules.class_battery import *
from modules.class_electricity_price import *
from modules.class_heatpump import * 
from modules.class_load_container import * 
from modules.class_summertime import *
from modules.class_soc_calc import *
from modules.render import *
#from modules.class_battery_soc_predictor import *
from modules.class_load_corrector import *
import os
from flask import Flask, send_from_directory
from pprint import pprint
import matplotlib
matplotlib.use('Agg')  # Setzt das Backend auf Agg
import matplotlib.pyplot as plt
import string
from datetime import datetime, timedelta
from deap import base, creator, tools, algorithms
from modules.class_optimize import *
import numpy as np
import random
import os
from config import *

app = Flask(__name__)

opt_class = optimization_problem(prediction_hours=prediction_hours, penalty=10, optimization_hours=optimization_hours)



# @app.route('/load_correction', methods=['GET'])
# def flask_load_correction():
    # if request.method == 'GET':
        # year_energy = float(request.args.get("year_energy"))
        # date_now,date = get_start_enddate(prediction_hours,startdate=datetime.now().date())
        # ###############
        # # Load Forecast
        # ###############
        # lf = LoadForecast(filepath=r'load_profiles.npz', year_energy=year_energy)
        # #power_haushalt = lf.get_daily_stats(date)[0,...]  # Datum anpassen
        # power_haushalt = lf.get_stats_for_date_range(date_now,date)[0] # Nur Erwartungswert!        
        
        # total_load = total_load(prediction_hours=prediction_hours)        
        # total_load.add("Haushalt", power_haushalt)

        # # ###############
        # # # WP
        # # ##############
        # # power_wp = wp.simulate_24h(temperaturee_forecast)
        # # total_load.add("Heatpump", power_wp)
                
        # load = total_load.calculate_total_load()
        # print(load)
        # #print(specific_date_prices)
        # return jsonify(load.tolist())


@app.route('/soc', methods=['GET'])
def flask_soc():

    # MariaDB Verbindungsdetails
    config = db_config

    # Parameter festlegen
    voltage_high_threshold = 55.4  # 100% SoC
    voltage_low_threshold = 46.5  # 0% SoC
    current_low_threshold = 2  # Niedriger Strom für beide Zustände
    gap = 30  # Zeitlücke in Minuten zum  Gruppieren von Maxima/Minima
    bat_capacity = 33 * 1000 / 48 

    # Zeitpunkt X definieren
    datetime_x = (datetime.now() - timedelta(weeks=3)).strftime('%Y-%m-%d %H:%M:%S')


    # BatteryDataProcessor instanziieren und verwenden
    processor = BatteryDataProcessor(config, voltage_high_threshold, voltage_low_threshold, current_low_threshold, gap,bat_capacity)
    processor.connect_db()
    processor.fetch_data(datetime_x)
    processor.process_data()
    load_points_100_df, load_points_0_df = processor.find_soc_points()
    soc_df, integration_results = processor.calculate_resetting_soc(load_points_100_df, load_points_0_df)
    #soh_df = processor.calculate_soh(integration_results)
    processor.update_database_with_soc(soc_df)
    #processor.plot_data(load_points_100_df, load_points_0_df, soc_df)
    processor.disconnect_db()
        
    return jsonify("Done")





@app.route('/electricity_price', methods=['GET'])
def flask_electricity_price():
        date_now,date = get_start_enddate(prediction_hours,startdate=datetime.now().date())
        filepath = os.path.join (r'test_data', r'electricity_prices_batterydokAPI.json')  # Pfad zur JSON-Datei anpassen
        #price_forecast = HourlyElectricityPriceForecast(source=filepath)
        price_forecast = HourlyElectricityPriceForecast(source="https://api.batterydoktor.net/prices?start="+date_now+"&end="+date+"", prediction_hours=prediction_hours)
        specific_date_prices = price_forecast.get_price_for_daterange(date_now,date)
        #print(specific_date_prices)
        return jsonify(specific_date_prices.tolist())



# Die letzten X gemessenen Daten + total_load Simple oder eine andere Schätung als Input
# Daraus wird dann eine neuen loadprognose erstellt welche korrigiert ist.
# Input: 
@app.route('/total_load', methods=['POST'])
def flask_total_load():
    # Daten aus dem JSON-Body abrufen
    data = request.get_json()

    # Extract year_energy and prediction_hours from the request JSON
    year_energy = float(data.get("year_energy"))
    prediction_hours = int(data.get("hours", 48))  # Default to 48 hours if not specified

    # Measured data as JSON
    measured_data_json = data.get("measured_data")

    # Convert JSON data into a Pandas DataFrame
    measured_data = pd.DataFrame(measured_data_json)
    # Make sure the 'time' column is in datetime format
    measured_data['time'] = pd.to_datetime(measured_data['time'])

    # Check if the datetime has timezone info, if not, assume it's local time
    if measured_data['time'].dt.tz is None:
        # Treat it as local time and localize it
        measured_data['time'] = measured_data['time'].dt.tz_localize('Europe/Berlin')
    else:
        # Convert the time to local timezone (e.g., 'Europe/Berlin')
        measured_data['time'] = measured_data['time'].dt.tz_convert('Europe/Berlin')

    # Remove timezone info after conversion
    measured_data['time'] = measured_data['time'].dt.tz_localize(None)
    
    # Instantiate LoadForecast and generate forecast data
    lf = LoadForecast(filepath=r'load_profiles.npz', year_energy=year_energy)

    # Generate forecast data based on the measured data time range
    forecast_list = []
    for single_date in pd.date_range(measured_data['time'].min().date(), measured_data['time'].max().date()):
        date_str = single_date.strftime('%Y-%m-%d')
        daily_forecast = lf.get_daily_stats(date_str)
        mean_values = daily_forecast[0]
        hours = [single_date + pd.Timedelta(hours=i) for i in range(24)]
        daily_forecast_df = pd.DataFrame({'time': hours, 'load Pred': mean_values})
        forecast_list.append(daily_forecast_df)

    # Concatenate all daily forecasts into a single DataFrame
    predicted_data = pd.concat(forecast_list, ignore_index=True)
    #print(predicted_data)
    # Create LoadPredictionAdjuster instance
    adjuster = LoadPredictionAdjuster(measured_data, predicted_data, lf)

    # Calculate weighted mean and adjust predictions
    adjuster.calculate_weighted_mean()
    adjuster.adjust_predictions()

    # Predict the next x hours
    future_predictions = adjuster.predict_next_hours(prediction_hours)

    # Extract the household power predictions
    power_haushalt = future_predictions['Adjusted Pred'].values

    # Instantiate total_load and add household power predictions
    total_load = total_load(prediction_hours=prediction_hours)        
    total_load.add("Haushalt", power_haushalt)

    # ###############
    # # WP (optional)
    # ###############
    # power_wp = wp.simulate_24h(temperaturee_forecast)
    # total_load.add("Heatpump", power_wp)
    
    # Calculate the total load
    load = total_load.calculate_total_load()

    # Return the calculated load as JSON
    return jsonify(load.tolist())




# @app.route('/total_load', methods=['GET'])
# def flask_total_load():
    # if request.method == 'GET':
        # year_energy = float(request.args.get("year_energy"))
        # prediction_hours = int(request.args.get("hours", 48))  # Default to 24 hours if not specified
        # date_now = datetime.now()
        # end_date = (date_now + timedelta(hours=prediction_hours)).strftime('%Y-%m-%d %H:%M:%S')

        # ###############
        # # Load Forecast
        # ###############
        # # Instantiate loadEstimator and get measured data
        # estimator = loadEstimator()
        # start_date = (date_now - timedelta(days=60)).strftime('%Y-%m-%d')  # Example: load 60 days
        # end_date = date_now.strftime('%Y-%m-%d')  # Current date

        # load_df = estimator.get_load(start_date, end_date)

        # selected_columns = load_df[['timestamp', 'load']]
        # selected_columns['time'] = pd.to_datetime(selected_columns['timestamp']).dt.floor('H')
        # selected_columns['load'] = pd.to_numeric(selected_columns['load'], errors='coerce')
        # cleaned_data = selected_columns.dropna()

        # # Instantiate LoadForecast
        # lf = LoadForecast(filepath=r'load_profiles.npz', year_energy=year_energy)

        # # Generate forecast data
        # forecast_list = []
        # for single_date in pd.date_range(cleaned_data['time'].min().date(), cleaned_data['time'].max().date()):
            # date_str = single_date.strftime('%Y-%m-%d')
            # daily_forecast = lf.get_daily_stats(date_str)
            # mean_values = daily_forecast[0]
            # hours = [single_date + pd.Timedelta(hours=i) for i in range(24)]
            # daily_forecast_df = pd.DataFrame({'time': hours, 'load Pred': mean_values})
            # forecast_list.append(daily_forecast_df)

        # forecast_df = pd.concat(forecast_list, ignore_index=True)

        # # Create LoadPredictionAdjuster instance
        # adjuster = LoadPredictionAdjuster(cleaned_data, forecast_df, lf)
        # adjuster.calculate_weighted_mean()
        # adjuster.adjust_predictions()

        # # Predict the next hours
        # future_predictions = adjuster.predict_next_hours(prediction_hours)

        # power_haushalt = future_predictions['Adjusted Pred'].values

        # total_load = total_load(prediction_hours=prediction_hours)        
        # total_load.add("Haushalt", power_haushalt)

        # # ###############
        # # # WP
        # # ##############
        # # power_wp = wp.simulate_24h(temperaturee_forecast)
        # # total_load.add("Heatpump", power_wp)
                
        # load = total_load.calculate_total_load()
        # print(load)
        # return jsonify(load.tolist())

             
@app.route('/total_load_simple', methods=['GET'])
def flask_total_load_simple():
    if request.method == 'GET':
        year_energy = float(request.args.get("year_energy"))
        date_now,date = get_start_enddate(prediction_hours,startdate=datetime.now().date())
        ###############
        # Load Forecast
        ###############
        lf = LoadForecast(filepath=r'load_profiles.npz', year_energy=year_energy)
        #power_haushalt = lf.get_daily_stats(date)[0,...]  # Datum anpassen
        power_haushalt = lf.get_stats_for_date_range(date_now,date)[0] # Nur Erwartungswert!        
        
        total_load = total_load(prediction_hours=prediction_hours)        
        total_load.add("Haushalt", power_haushalt)

        # ###############
        # # WP
        # ##############
        # power_wp = wp.simulate_24h(temperaturee_forecast)
        # total_load.add("Heatpump", power_wp)
                
        load = total_load.calculate_total_load()
        print(load)
        #print(specific_date_prices)
        return jsonify(load.tolist())

@app.route('/pvforecast', methods=['GET'])
def flask_pvprognose():
    if request.method == 'GET':
        url = request.args.get("url")
        ac_power_measurement = request.args.get("ac_power_measurement")
        date_now,date = get_start_enddate(prediction_hours,startdate=datetime.now().date())
        
        ###############
        # PV Forecast
        ###############
        PVforecast = PVForecast(prediction_hours = prediction_hours, url=url)
        #print("PVPOWER",parameter['pvpowernow'])
        if isfloat(ac_power_measurement):
            PVforecast.update_ac_power_measurement(date_time=datetime.now(), ac_power_measurement=float(ac_power_measurement) )
            #PVforecast.print_ac_power_and_measurement()
        
        pv_forecast = PVforecast.get_pv_forecast_for_date_range(date_now,date) #get_forecast_for_date(date)
        temperaturee_forecast = PVforecast.get_temperaturee_for_date_range(date_now,date)

        #print(specific_date_prices)
        ret = {"temperaturee":temperaturee_forecast.tolist(),"pvpower":pv_forecast.tolist()}
        return jsonify(ret)


@app.route('/optimize', methods=['POST'])
def flask_optimize():
    if request.method == 'POST':
        parameter = request.json
        
        # Erforderliche Parameter prüfen
        erforderliche_parameter = [ 'preis_euro_pro_wh_battery','electricity_price_euro_per_wh', "total_load",'pv_battery_cap', "feed_in_tariff_euro_per_wh
",  'pv_forecast','temperaturee_forecast', 'bev_min_soc', "bev_cap","bev_charge_efficiency","bev_charge_power","bev_soc","pv_soc","start_solution","household_appliance_duration","household_appliance_wh"]
        for p in erforderliche_parameter:
            if p not in parameter:
                return jsonify({"error": f"Fehlender Parameter: {p}"}), 400

        # Simulation durchführen
        ergebnis = opt_class.optimization_ems(parameter=parameter, start_hour=datetime.now().hour) # , startdate = datetime.now().date() - timedelta(days = 1)
        
        return jsonify(ergebnis)


@app.route('/rendered_results.pdf')
def get_pdf():
    return send_from_directory('', 'rendered_results.pdf')


@app.route("/site-map")
def site_map():
    def print_links(links):
        ### This is lazy. Use templates
        content = "<h1>Valid routes</h1><ul>"
        for link in links:
            content += f"<li><a href='{link}'>{link}</li>"
        content = content + "<ul>"
        return content

    def has_no_empty_params(rule):
        defaults = rule.defaults if rule.defaults is not None else ()
        arguments = rule.arguments if rule.arguments is not None else ()
        return len(defaults) >= len(arguments)
    links = []
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append(url)
    return print_links(sorted(links))

@app.route('/')
def root():
    return redirect("/site-map", code=302)


if __name__ == '__main__':
    try:
        host= os.getenv("FLASK_RUN_HOST", "0.0.0.0")
        port = os.getenv("FLASK_RUN_PORT", 5000)
        app.run(debug=True, host=host, port=port)
    except:
        print(f"Coud not bind to host {host}:{port}, set FLASK_RUN_HOST and/or FLASK_RUN_PORT.")


# PV Forecast:
#   object {
#    pvpower: array[48]
#    temperaturee: array[48]
#   }
