import numpy as np
import gettext
import os

class PVBattery:
    def __init__(self, capacity_wh=None, hours=None, charging_efficiency=0.88, discharging_efficiency=0.88,max_charging_power_w=None,initial_soc_percentage=0,min_soc_percentage=0,max_soc_percentage=100):
        # Kapazität des batterys in Wh
        self.capacity_wh = capacity_wh
        # Initialer charge_level des batterys in Wh
        self.initial_soc_percentage = initial_soc_percentage
        self.soc_wh = (initial_soc_percentage / 100) * capacity_wh
        self.hours = hours
        self.discharge_array = np.full(self.hours, 1)
        self.charge_array = np.full(self.hours, 1)
        # Lade- und Entladeeffizienz
        self.charging_efficiency = charging_efficiency
        self.discharging_efficiency = discharging_efficiency        
        self.max_charging_power_w = max_charging_power_w if max_charging_power_w else self.capacity_wh
        self.min_soc_percentage = min_soc_percentage
        self.max_soc_percentage = max_soc_percentage
        

    def to_dict(self):
        return {
            "capacity_wh": self.capacity_wh,
            "initial_soc_percentage": self.initial_soc_percentage,
            "soc_wh": self.soc_wh,
            "hours": self.hours,
            "discharge_array": self.discharge_array.tolist(),  # Umwandlung von np.array in Liste
            "charge_array": self.charge_array.tolist(),
            "charging_efficiency": self.charging_efficiency,
            "discharging_efficiency": self.discharging_efficiency,
            "max_charging_power_w": self.max_charging_power_w
        }

    @classmethod
    def from_dict(cls, data):
        # Create a new instance of the class
        obj = cls(
            capacity_wh=data["capacity_wh"],
            hours=data["hours"],
            charging_efficiency=data["charging_efficiency"],
            discharging_efficiency=data["discharging_efficiency"],
            max_charging_power_w=data["max_charging_power_w"],
            initial_soc_percentage=data["initial_soc_percentage"]
        )
        # Set the remaining attributes
        obj.discharge_array = np.array(data["discharge_array"])
        obj.charge_array = np.array(data["charge_array"])
        obj.soc_wh = data["soc_wh"]  # Set the state of charge
        
        return obj


    def reset(self):
        self.soc_wh = (self.initial_soc_percentage / 100) * self.capacity_wh
        self.discharge_array = np.full(self.hours, 1)
        self.charge_array = np.full(self.hours, 1)
        
    def set_discharge_per_hour(self, discharge_array):
        assert(len(discharge_array) == self.hours)
        self.discharge_array = np.array(discharge_array)

    def set_charge_per_hour(self, charge_array):
        assert(len(charge_array) == self.hours)
        self.charge_array = np.array(charge_array)

    def charge_level_percentage(self):
        return (self.soc_wh / self.capacity_wh) * 100

    def energie_abgeben(self, wh, hour):
        if self.discharge_array[hour] == 0:
            return 0.0, 0.0  # No energy discharge, no losses
        
        # Calculate the maximum energy that can be discharged
        max_discharge_capacity_wh = self.soc_wh * self.discharging_efficiency
        
        # The maximum discharge capacity is limited by the maximum discharge power
        max_discharge_capacity_wh = min(max_discharge_capacity_wh, self.max_charging_power_w)
        
        
        # Calculate the actual energy that can be discharged
        discharged_wh = min(wh, max_discharge_capacity_wh)
        
        # Calculate the actual energy that was discharged (without losses)
        extraction_wh = discharged_wh / self.discharging_efficiency
        
        # Update SOC
        self.soc_wh -= extraction_wh
        
        # Calculate losses
        losses_wh = extraction_wh - discharged_wh
        
        # Return the actual energy that was discharged and the losses
        return discharged_wh, losses_wh

        # return soc_tmp-self.soc_wh



    def charge_energy(self, wh, hour):
        if hour is not None and self.charge_array[hour] == 0:
            return 0,0  # Charging dissallowed in this hour

        # if wh is unset, use the maximum charging power
        wh = wh if wh is not None else self.max_charging_power_w
        
        # Relativ zur maximalen charging_power (zwischen 0 und 1)
        relative_charging_power = self.charge_array[hour]
        effective_charging_power = relative_charging_power * self.max_charging_power_w

        # Berechnung der tatsächlichen Lademenge unter Berücksichtigung der Ladeeffizienz
        effective_charging_amount = min(wh, effective_charging_power) 

        # Aktualisierung des charge_levels ohne die Kapazität zu überschreiten
        charged_amount_without_losses = min(self.capacity_wh - self.soc_wh, effective_charging_amount)

        charged_amount = charged_amount_without_losses * self.charging_efficiency

        
        self.soc_wh += charged_amount
    
        losses_wh = charged_amount_without_losses* (1.0-self.charging_efficiency)


        return charged_amount, losses_wh

    def current_energy_content(self):
        """
        Diese Methode gibt die aktuelle Restenergie unter Berücksichtigung des Wirkungsgrades zurück.
        Sie berücksichtigt dabei die Lade- und Entladeeffizienz.
        """
        # Berechnung der Restenergie unter Berücksichtigung der Entladeeffizienz
        usable_energy = self.soc_wh * self.discharging_efficiency
        return usable_energy




    # def charge_energy(self, wh, hour):
        # if hour is not None and self.charge_array[hour] == 0:
            # return 0,0  # Ladevorgang in dieser hour nicht erlaubt

        # # Wenn kein Wert für wh angegeben wurde, verwende die maximale charging_power
        # wh = wh if wh is not None else self.max_charging_power_w

        # # Berechnung der tatsächlichen Lademenge unter Berücksichtigung der Ladeeffizienz
        # effective_charging_amount = min(wh, self.max_charging_power_w) 

        # # Aktualisierung des charge_levels ohne die Kapazität zu überschreiten
        # charged_amount_without_losses = min(self.capacity_wh - self.soc_wh, effective_charging_amount)

        # charged_amount = charged_amount_without_losses * self.charging_efficiency

        
        # self.soc_wh += charged_amount
    
        # losses_wh = charged_amount_without_losses* (1.0-self.charging_efficiency)
        

        
        # # Zusätzliche losses, wenn die Energiezufuhr die Kapazitätsgrenze überschreitet
        # # zusatz_losses_wh = 0
        # # if effective_charging_amount > charged_amount_without_losses:
            # # zusatz_losses_wh = (effective_charging_amount - charged_amount_without_losses) * self.charging_efficiency
        
        # # # Gesamtlosses berechnen
        # # gesamt_losses_wh = losses_wh + zusatz_losses_wh
        
        
        # return charged_amount, losses_wh
        # # effective_charging_amount = wh * self.charging_efficiency
        # # self.soc_wh = min(self.soc_wh + effective_charging_amount, self.capacity_wh)




if __name__ == '__main__':
    
    locale_path = os.path.join(os.path.dirname(__file__), 'locale')
    language = gettext.translation('messages', localedir=locale_path, languages=['de'])
    language.install()
    _ = language.gettext
    # Example usage
    battery = PVBattery(10000) # A 10.000Wh Battery
    print(_("initial charge_level: {charge_level}%").format(charge_level=battery.charge_level_percentage()))

    battery.charge_energy(5000)
    print(f"charge_level after charge: {battery.charge_level_percentage()}%, Aktueller Energieinhalt: {battery.current_energy_content()} Wh")

    delivered_energy = battery.energie_abgeben(3000)
    print(f"Deliverd energy: {delivered_energy} Wh, charge level afterwards: {battery.charge_level_percentage()}%, Current energy content: {battery.current_energy_content()} Wh")

    battery.charge_energy(6000)
    print(f"charge_level after weiterem Laden: {battery.charge_level_percentage()}%, Aktueller Energieinhalt: {battery.current_energy_content()} Wh")
