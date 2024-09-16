from datetime import datetime
import numpy as np

def replace_nan_with_none(data):
    if isinstance(data, dict):
        return {key: replace_nan_with_none(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [replace_nan_with_none(element) for element in data]
    elif isinstance(data, float) and np.isnan(data):
        return None
    else:
        return data



class EneryManagementSystem:
    def __init__(self,  pv_forecast_wh=None, electricity_price_euro_per_wh=None, feed_in_tariff_euro_per_wh
=None, bev=None, total_load=None, household_appliance=None, inverter=None):
        self.battery = inverter.battery
        #self.load_curve_wh = load_curve_wh
        self.total_load = total_load
        self.pv_forecast_wh = pv_forecast_wh
        self.electricity_price_euro_per_wh = electricity_price_euro_per_wh  # electricity_price in Cent pro Wh
        self.feed_in_tariff_euro_per_wh = feed_in_tariff_euro_per_wh
  # Einspeisevergütung in Cent pro Wh
        self.bev = bev
        self.household_appliance = household_appliance
        self.inverter = inverter
        
        
    
    def set_battery_discharge_hours(self, ds):
        self.battery.set_discharge_per_hour(ds)
    
    def set_bev_charge_hours(self, ds):
        self.bev.set_charge_per_hour(ds)

    def set_household_appliance_start(self, ds, global_start_hour=0):
        self.household_appliance.set_start_time(ds,global_start_hour=global_start_hour)
        
    def reset(self):
        self.bev.reset()
        self.battery.reset()

    def simulate_from_now(self):
        jetzt = datetime.now()
        starting_hour = jetzt.hour
        # Berechne die Anzahl der hours bis zum gleichen Zeitpunkt am nächsten Tag
        # hours_bis_ende_tag = 24 - starting_hour
        # Füge diese hours zum nächsten Tag hinzu
        #gesamt_hours = hours_bis_ende_tag + 24

        # Beginne die Simulation ab der aktuellen hour und führe sie für die berechnete duration aus
        return self.simulate(starting_hour)


    def simulate(self, starting_hour):
        load_wh_per_hour = []
        feed_in_wh_per_hour = []
        grid_consumption_wh_per_hour = []
        cost_euro_per_hour = []
        earnings_euro_per_hour = []
        battery_soc_per_hour = []
        bev_soc_per_hour = []
        losses_wh_per_hour = []
        household_appliance_wh_per_hour = []
        load_curve_wh = self.total_load
        
        
        assert len(load_curve_wh) == len(self.pv_forecast_wh) == len(self.electricity_price_euro_per_wh), f"Arraygrößen stimmen nicht überein: load_curve = {len(load_curve_wh)}, PV-Prognose = {len(self.pv_forecast_wh)}, electricity_price = {len(self.electricity_price_euro_per_wh)}"

        ende = min( len(load_curve_wh),len(self.pv_forecast_wh), len(self.electricity_price_euro_per_wh))

        # Endzustände auf NaN setzen, damit diese übersprungen werden für die hour
        load_wh_per_hour.append(np.nan)
        feed_in_wh_per_hour.append(np.nan)
        grid_consumption_wh_per_hour.append(np.nan) 
        cost_euro_per_hour.append(np.nan) 
        battery_soc_per_hour.append(self.battery.charge_level_percentage()) 
        earnings_euro_per_hour.append(np.nan) 
        bev_soc_per_hour.append(self.bev.charge_level_percentage())
        losses_wh_per_hour.append(np.nan)
        household_appliance_wh_per_hour.append(np.nan)
        
        # Berechnet das Ende basierend auf der Länge der load_curve
        for hour in range(starting_hour+1, ende):
        
            # Zustand zu Beginn der hour (Anfangszustand)
            battery_soc_start = self.battery.charge_level_percentage()  # Anfangszustand battery-SoC
            if self.bev:
                bev_soc_start = self.bev.charge_level_percentage()  # Anfangszustand E-Auto-SoC


        
            # Anpassung, um sicherzustellen, dass Indizes korrekt sind
            consumption = load_curve_wh[hour]   # consumption für die hour
            if self.household_appliance != None:
                consumption = consumption + self.household_appliance.get_load_for_hour(hour)
                household_appliance_wh_per_hour.append(self.household_appliance.get_load_for_hour(hour))
            else: 
                household_appliance_wh_per_hour.append(0)
            generation = self.pv_forecast_wh[hour]
            electricity_price = self.electricity_price_euro_per_wh[hour] if hour < len(self.electricity_price_euro_per_wh) else self.electricity_price_euro_per_wh[-1]
            
            losses_wh_per_hour.append(0.0)

            # Logik für die E-Auto-Ladung bzw. Entladung
            if self.bev:  # Falls ein E-Auto vorhanden ist
                charged_amount_bev, losses_bev = self.bev.charge_energy(None,hour)
                consumption = consumption + charged_amount_bev
                losses_wh_per_hour[-1] += losses_bev
                bev_soc = self.bev.charge_level_percentage()


            
            stündlicher_grid_consumption_wh = 0
            hourly_cost_eur = 0
            hourly_income_eur = 0

            #Wieviel kann der WR 
            grid_feed_in, grid_consumption,  losses, own_consumption = self.inverter.process_energy(generation, consumption, hour)
            
            # Speichern
            feed_in_wh_per_hour.append(grid_feed_in)
            hourly_income_eur = grid_feed_in* self.feed_in_tariff_euro_per_wh[hour] 
            
            hourly_cost_eur = grid_consumption * electricity_price 
            grid_consumption_wh_per_hour.append(grid_consumption)
            losses_wh_per_hour[-1] += losses
            load_wh_per_hour.append(own_consumption + grid_consumption)
            

            
            if self.bev:
                bev_soc_per_hour.append(bev_soc)
            
            battery_soc_per_hour.append(self.battery.charge_level_percentage())
         
            cost_euro_per_hour.append(hourly_cost_eur)
            earnings_euro_per_hour.append(hourly_income_eur)


        gesamtkosten_euro = np.nansum(cost_euro_per_hour) - np.nansum(earnings_euro_per_hour)
        expected_length = ende - starting_hour
        array_names = ['own_consumption_Wh_per_hour', 'feed_in_wh_per_hour', 'grid_consumption_wh_per_hour', 'cost_euro_per_hour', 'battery_soc_per_hour', 'earnings_euro_per_hour','E-Auto_SoC_per_hour', "losses_per_hour"]
        all_arrays = [load_wh_per_hour, feed_in_wh_per_hour, grid_consumption_wh_per_hour, cost_euro_per_hour, battery_soc_per_hour, earnings_euro_per_hour,bev_soc_per_hour,losses_wh_per_hour]

        inconsistent_arrays = [name for name, arr in zip(array_names, all_arrays) if len(arr) != expected_length]
        #print(inconsistent_arrays)
        
        if inconsistent_arrays:
            raise ValueError(f"Inkonsistente Längen bei den Arrays: {', '.join(inconsistent_arrays)}. Erwartete Länge: {expected_length}, gefunden: {[len(all_arrays[array_names.index(name)]) for name in inconsistent_arrays]}")

        out = {
            'load_wh_per_hour': load_wh_per_hour,
            'feed_in_wh_per_hour': feed_in_wh_per_hour,
            'grid_consumption_wh_per_hour': grid_consumption_wh_per_hour,
            'cost_euro_per_hour': cost_euro_per_hour,
            'battery_soc_per_hour': battery_soc_per_hour,
            'earnings_euro_per_hour': earnings_euro_per_hour,
            'overall_balance_Euro': gesamtkosten_euro,
            'E-Auto_SoC_per_hour':bev_soc_per_hour,
            'Gesamteinnahmen_Euro': np.nansum(earnings_euro_per_hour),
            'Gesamtkosten_Euro': np.nansum(cost_euro_per_hour),
            "losses_per_hour":losses_wh_per_hour,
            "Gesamt_losses":np.nansum(losses_wh_per_hour),
            "household_appliance_wh_per_hour":household_appliance_wh_per_hour
        }
        
        out = replace_nan_with_none(out)
        
        return out
