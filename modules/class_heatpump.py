import json
from datetime import datetime, timedelta, timezone
import numpy as np
from pprint import pprint


class Heatpump:
    def __init__(self, max_heating_power, prediction_hours):
        self.max_heating_power = max_heating_power
        self.prediction_hours = prediction_hours

    def cop_berechnen(self, outdoor_temperature):
        cop = 3.0 + (outdoor_temperature-0) * 0.1
        return max(cop, 1)


    def calculate_heating_power(self, outdoor_temperature):
        #235.092 kWh + temperature * -11.645
        heating_power = (((235.0) + outdoor_temperature*(-11.645))*1000)/24.0
        heating_power = min(self.max_heating_power,heating_power)
        return heating_power

    def calculate_electric_power(self, outdoor_temperature):
        #heating_power = self.calculate_heating_power(outdoor_temperature)
        #cop = self.cop_berechnen(outdoor_temperature)
        
        return 1164  -77.8*outdoor_temperature + 1.62*outdoor_temperature**2.0
        #1253.0*np.math.pow(outdoor_temperature,-0.0682)

    def simulate_24h(self, temperatures):
        power_data = []
        
        # Überprüfen, ob das temperaturearray die richtige Größe hat
        if len(temperatures) != self.prediction_hours:
            raise ValueError("Das temperature array muss genau "+str(self.prediction_hours)+" Einträge enthalten, einen für jede hour des Tages.")
        
        for temp in temperatures:
            electric_power = self.calculate_electric_power(temp)
            power_data.append(electric_power)
        return power_data






# Beispiel für die Verwendung der Klasse
if __name__ == '__main__':
        max_heating_power = 5000  # 5 kW heating_power
        start_innentemperature = 15
        isolationseffizienz = 0.8
        gewuenschte_innentemperature = 20
        wp = Heatpump(max_heating_power)
        
        print(wp.cop_berechnen(-10)," ",wp.cop_berechnen(0), " ", wp.cop_berechnen(10))
        # 24 hours Außentemperatures (Beispielwerte)
        temperatures = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -5, -2, 5]

        # Berechnung der 24-hours-power_data
        power_data = wp.simulate_24h(temperatures)

        print(power_data)
