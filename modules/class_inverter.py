class inverter:
    def __init__(self, max_power_wh, battery):
        self.max_power_wh = max_power_wh  # Maximale power, die der inverter verarbeiten kann
        self.battery = battery  # Verbindung zu einem battery-Objekt

    def process_energy(self, generation, consumption, hour):
        losses = 0
        grid_feed_in = 0
        grid_consumption = 0.0
        own_consumption = 0.0
        #own_consumption = min(generation, consumption)  # Direkt consumptionte Energie

        if generation >= consumption:
            if consumption > self.max_power_wh:

                losses += generation - self.max_power_wh
                remaining_power_after_consumption = self.max_power_wh - consumption                
                grid_consumption = -remaining_power_after_consumption
                own_consumption = self.max_power_wh
                
            else: 
                # if hour==10:
                    # print("PV:",generation)
                    # print("Load:",consumption)
                    # print("Max Leist:",self.max_power_wh)
                # PV > WR power dann Verlust
                
                # Load
                remaining_power_after_consumption = generation-consumption #min(self.max_power_wh - consumption, generation-consumption)
                # battery
                charged_energy, charging_losses_battery = self.battery.charge_energy(remaining_power_after_consumption, hour)
                remaining_power_excess = remaining_power_after_consumption - (charged_energy+charging_losses_battery)
                # if hour == 1:
                    # print("generation:",generation)
                    # print("load:",consumption)
                    # print("battery:",charged_energy)
                    # print("battery:",self.battery.charge_level_percentage())
                    # print("RestÜberschuss"," - ",remaining_power_excess)
                    # print("RestLesitung WR:",self.max_power_wh - consumption)
                # feed_in, restliche WR Kapazität
               
                if remaining_power_excess > self.max_power_wh - consumption:
                    grid_feed_in = self.max_power_wh - consumption
                    losses += remaining_power_excess - grid_feed_in
                else:
                    grid_feed_in = remaining_power_excess
                #if hour ==14:
                #    print("Erz:",generation," load:",consumption, " RestPV:",remaining_power_excess," ",remaining_power_after_consumption, " Gela:",charged_energy," Ver:",charging_losses_battery," Einsp:",grid_feed_in)
                losses += charging_losses_battery

                
                
                own_consumption = consumption
 
        else:
            power_needed = consumption - generation
            max_battery_power = self.battery.max_charging_power_w
            
            #rest_ac_power = max(max_battery_power - generation,0)
            rest_ac_power = max(self.max_power_wh - generation,0)
            
            if power_needed < rest_ac_power:
                aus_battery, battery_entladelosses = self.battery.energie_abgeben(power_needed, hour)
            else: 
                aus_battery, battery_entladelosses = self.battery.energie_abgeben(rest_ac_power, hour)
            
            
            losses += battery_entladelosses

            grid_consumption = power_needed - aus_battery
            own_consumption = generation + aus_battery


        return grid_feed_in, grid_consumption, losses, own_consumption
