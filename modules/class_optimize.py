from flask import Flask, jsonify, request
import numpy as np
from  modules.class_load import *
from  modules.class_ems import *
from  modules.class_pv_forecast import *
from modules.class_battery import *

from modules.class_heatpump import * 
from modules.class_load_container import * 
from modules.class_inverter import * 
from modules.class_summertime import *
from modules.render import *
from modules.class_household_appliance import *
import os
from flask import Flask, send_from_directory
from pprint import pprint
import matplotlib
matplotlib.use('Agg')  # Setzt das Backend auf Agg
import matplotlib.pyplot as plt
import string
from datetime import datetime
from deap import base, creator, tools, algorithms
import numpy as np
import random
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

def isfloat(num):
    try:
        float(num)
        return True
    except:
        return False

def differential_evolution(population, toolbox, cxpb, mutpb, ngen, stats=None, halloffame=None, verbose=__debug__):
    """Differential Evolution Algorithm"""
    
    # Evaluate the entire population
    fitnesses = list(map(toolbox.evaluate, population))
    for ind, fit in zip(population, fitnesses):
        ind.fitness.values = fit
    
    if halloffame is not None:
        halloffame.update(population)
    
    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

    for gen in range(ngen):
        # Generate the next generation by mutation and recombination
        for i, target in enumerate(population):
            a, b, c = random.sample([ind for ind in population if ind != target], 3)
            mutant = toolbox.clone(a)
            for k in range(len(mutant)):
                mutant[k] = c[k] + mutpb * (a[k] - b[k])  # Mutation step
                if random.random() < cxpb:  # Recombination step
                    mutant[k] = target[k]
            
            # Evaluate the mutant
            mutant.fitness.values = toolbox.evaluate(mutant)
            
            # Replace if mutant is better
            if mutant.fitness > target.fitness:
                population[i] = mutant

        # Update hall of fame
        if halloffame is not None:
            halloffame.update(population)

        # Gather all the fitnesses in one list and print the stats
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(population), **record)
        if verbose:
            print(logbook.stream)
    
    return population, logbook



class optimization_problem:
    def __init__(self, prediction_hours=24, penalty = 10, optimization_hours= 24):
        self.prediction_hours = prediction_hours#
        self.penalty = penalty
        self.opti_param = None
        self.fixed_bev_hours = prediction_hours-optimization_hours
        self.possible_charge_values = possible_charging_currents_percentage


    def split_individual(self, individual):
        """
        Teilt das gegebene Individuum in die verschiedenen Parameter auf: 
        - Entladeparameter (discharge_hours_bin)
        - Ladeparameter (bevcharge_hours_float)
        - Haushaltsgeräte (spuelstart_int, falls vorhanden)
        """
        # Extrahiere die Entlade- und Ladeparameter direkt aus dem Individuum
        discharge_hours_bin = individual[:self.prediction_hours]  # Erste 24 Werte sind Bool (Entladen)
        bevcharge_hours_float = individual[self.prediction_hours:self.prediction_hours * 2]  # Nächste 24 Werte sind Float (Laden)

        spuelstart_int = None
        if self.opti_param and self.opti_param.get("household_appliances", 0) > 0:
            spuelstart_int = individual[-1]  # Letzter Wert ist Startzeit für Haushaltsgerät

        return discharge_hours_bin, bevcharge_hours_float, spuelstart_int


    def setup_deap_environment(self,opti_param, start_hour):
        self.opti_param = opti_param
  
        
        if "FitnessMin" in creator.__dict__:
                del creator.FitnessMin
        if "Individual" in creator.__dict__:
                del creator.Individual

        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)
        
        # PARAMETER
        self.toolbox = base.Toolbox()
        self.toolbox.register("attr_bool", random.randint, 0, 1)
        self.toolbox.register("attr_float", random.uniform, 0, 1)  # Für kontinuierliche Werte zwischen 0 und 1 (z.B. für E-Auto-charging_power)
        #self.toolbox.register("attr_choice", random.choice, self.possible_charge_values)  # Für diskrete Ladeströme

        self.toolbox.register("attr_int", random.randint, start_hour, 23)
        
        
        
        ###################
        # household_appliances
        #print("Haushalt:",opti_param["household_appliances"])
        if opti_param["household_appliances"]>0:   
                def create_individual():
                        attrs = [self.toolbox.attr_bool() for _ in range(self.prediction_hours)]  # 24 Bool-Werte für Entladen
                        attrs += [self.toolbox.attr_float()  for _ in range(self.prediction_hours)]  # 24 Float-Werte für Laden
                        attrs.append(self.toolbox.attr_int())  # Haushaltsgerät-Startzeit
                        return creator.Individual(attrs)

        else:
                def create_individual():
                        attrs = [self.toolbox.attr_bool() for _ in range(self.prediction_hours)]  # 24 Bool-Werte für Entladen
                        attrs += [self.toolbox.attr_float()  for _ in range(self.prediction_hours)]  # 24 Float-Werte für Laden
                        return creator.Individual(attrs)

                

        self.toolbox.register("individual", create_individual)#tools.initCycle, creator.Individual, (self.toolbox.attr_bool,self.toolbox.attr_bool), n=self.prediction_hours+1)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutFlipBit, indpb=0.1)
        
        
        
        #self.toolbox.register("mutate", mutate_choice, self.possible_charge_values, indpb=0.1)
        #self.toolbox.register("mutate", tools.mutUniformInt, low=0, up=len(self.possible_charge_values)-1, indpb=0.1)

        self.toolbox.register("select", tools.selTournament, tournsize=3)    
        
    def evaluate_inner(self,individual, ems,start_hour):
        ems.reset()
        
        #print("Spuel:",self.opti_param)

        discharge_hours_bin, bevcharge_hours_float, spuelstart_int = self.split_individual(individual)        

        # household_appliances
        if self.opti_param["household_appliances"]>0:   
                ems.set_household_appliance_start(spuelstart_int,global_start_hour=start_hour)



        #discharge_hours_bin = np.full(self.prediction_hours,0)
        ems.set_battery_discharge_hours(discharge_hours_bin)
        
        # Setze die festen Werte für die letzten x hours
        for i in range(self.prediction_hours - self.fixed_bev_hours, self.prediction_hours):
            bevcharge_hours_float[i] = 0.0  # Setze die letzten x hours auf einen festen Wert (oder vorgegebenen Wert)

        #print(bevcharge_hours_float)
        
        ems.set_bev_charge_hours(bevcharge_hours_float)
        
        
        o = ems.simulate(start_hour)

        return o

    # Fitness-Funktion (muss Ihre EnergieManagementSystem-Logik integrieren)
    def evaluate(self,individual,ems,parameter,start_hour,worst_case):

        try:
                o = self.evaluate_inner(individual,ems,start_hour)
        except: 
                return (100000.0,)
                
        overall_balance = o["overall_balance_Euro"]
        if worst_case:
                overall_balance = overall_balance * -1.0
        
        discharge_hours_bin, bevcharge_hours_float, spuelstart_int = self.split_individual(individual)     
        max_charging_power = np.max(possible_charging_currents_percentage)

        penalty_überschreitung = 0.0

        # charging_power überschritten?
        for charging_power in bevcharge_hours_float:
                if charging_power > max_charging_power:
                    # Berechne die Überschreitung
                    überschreitung = charging_power - max_charging_power
                    # Füge eine penalty hinzu (z.B. 10 Einheiten penalty pro Prozentpunkt Überschreitung)
                    penalty_überschreitung += self.penalty * 10  # Hier ist die penalty proportional zur Überschreitung

        
        # Für jeden Discharge 0, eine kleine penalty von 1 Cent, da die loadvertelung noch fehlt. Also wenn es egal ist, soll er den battery entladen lassen
        for i in range(0, self.prediction_hours):
            if discharge_hours_bin[i] == 0.0:  # Wenn die letzten x hours von einem festen Wert abweichen
                overall_balance += 0.01  # Bepenalty den Optimierer
                
        
        # E-Auto nur die ersten self.fixed_bev_hours 
        for i in range(self.prediction_hours - self.fixed_bev_hours, self.prediction_hours):
            if bevcharge_hours_float[i] != 0.0:  # Wenn die letzten x hours von einem festen Wert abweichen
                overall_balance += self.penalty  # Bepenalty den Optimierer
        
        
        # Überprüfung, ob der Mindest-SoC erreicht wird
        final_soc = ems.bev.charge_level_percentage()  # Nimmt den SoC am Ende des optimizationszeitraums
        
        if (parameter['bev_min_soc']-ems.bev.charge_level_percentage()) <= 0.0:
                #print (parameter['bev_min_soc']," " ,ems.bev.charge_level_percentage()," ",(parameter['bev_min_soc']-ems.bev.charge_level_percentage()))
                for i in range(0, self.prediction_hours):
                    if bevcharge_hours_float[i] != 0.0:  # Wenn die letzten x hours von einem festen Wert abweichen
                        overall_balance += self.penalty  # Bepenalty den Optimierer

        
        bev_roi =  (parameter['bev_min_soc']-ems.bev.charge_level_percentage())
        individual.extra_data = (o["overall_balance_Euro"],o["Gesamt_losses"], bev_roi )
        
        
        restenergie_battery = ems.battery.current_energy_content()
        restwert_battery = restenergie_battery*parameter["preis_euro_pro_wh_battery"]
        # print(restenergie_battery)
        # print(parameter["preis_euro_pro_wh_battery"])
        # print(restwert_battery)
        # print()
        penalty = 0.0
        penalty = max(0,(parameter['bev_min_soc']-ems.bev.charge_level_percentage()) * self.penalty ) 
        overall_balance += penalty - restwert_battery + penalty_überschreitung
        #overall_balance += o["Gesamt_losses"]/10000.0
                
        return (overall_balance,)





    # Genetischer Algorithmus
    def optimize(self,start_solution=None):


        population = self.toolbox.population(n=300)
        hof = tools.HallOfFame(1)
        
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        print("Start:",start_solution)
        
        if start_solution is not None and start_solution != -1:
                population.insert(0, creator.Individual(start_solution))     
                population.insert(1, creator.Individual(start_solution))
                population.insert(2, creator.Individual(start_solution))
        
        algorithms.eaMuPlusLambda(population, self.toolbox, mu=100, lambda_=200, cxpb=0.5, mutpb=0.3, ngen=400,   stats=stats, halloffame=hof, verbose=True)
        #algorithms.eaSimple(population, self.toolbox, cxpb=0.3, mutpb=0.3, ngen=200,             stats=stats, halloffame=hof, verbose=True)
        #algorithms.eaMuCommaLambda(population, self.toolbox, mu=100, lambda_=200, cxpb=0.2, mutpb=0.4, ngen=300, stats=stats, halloffame=hof, verbose=True)
        #population, log = differential_evolution(population, self.toolbox, cxpb=0.2, mutpb=0.5, ngen=200, stats=stats, halloffame=hof, verbose=True)
        

        

        
        member = {"balance":[],"losses":[],"side_condition":[]}
        for ind in population:
                if hasattr(ind, 'extra_data'):
                        extra_value1, extra_value2,extra_value3 = ind.extra_data
                        member["balance"].append(extra_value1)
                        member["losses"].append(extra_value2)
                        member["side_condition"].append(extra_value3)
        
        
        return hof[0], member


    def optimization_ems(self,parameter=None, start_hour=None,worst_case=False, startdate=None):

        
        ############
        # Parameter 
        ############
        if startdate == None:
                date = (datetime.now().date() + timedelta(hours = self.prediction_hours)).strftime("%Y-%m-%d")
                date_now = datetime.now().strftime("%Y-%m-%d")
        else:
                date = (startdate + timedelta(hours = self.prediction_hours)).strftime("%Y-%m-%d")
                date_now = startdate.strftime("%Y-%m-%d")
        #print("Start_date:",date_now)
        
        battery_size = parameter['pv_battery_cap'] # Wh
       
        feed_in_tariff_euro_per_wh = np.full(self.prediction_hours, parameter["feed_in_tariff_euro_per_wh"])  #=  # € / Wh 7/(1000.0*100.0)
        discharge_array = np.full(self.prediction_hours,1) #np.array([1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0])   # 
        battery = PVbattery(capacity_wh=battery_size,hours=self.prediction_hours,initial_soc_percentage=parameter["pv_soc"], max_charging_power_w=5000)
        battery.set_charge_per_hour(discharge_array)
        
        
        charging_possible = np.full(self.prediction_hours,1) # np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0])
        bev = PVbattery(capacity_wh=parameter["bev_cap"], hours=self.prediction_hours, charging_efficiency=parameter["bev_charge_efficiency"], discharging_efficiency=1.0, max_charging_power_w=parameter["bev_charge_power"] ,initial_soc_percentage=parameter["bev_soc"])
        bev.set_charge_per_hour(charging_possible)
        min_soc_bev = parameter['bev_min_soc']
        start_params = parameter['start_solution']
        
        ###############
        # dishwasher
        ##############
        print(parameter)
        if parameter["household_appliance_duration"] >0:
                dishwasher = household_appliance(hours=self.prediction_hours, consumption_kwh=parameter["household_appliance_wh"], duration_h=parameter["household_appliance_duration"])
                dishwasher.set_start_time(start_hour)  # Startet jetzt
        else: 
                dishwasher = None



        
        

        


        ###############
        # PV Forecast
        ###############
        #PVforecast = PVForecast(filepath=os.path.join(r'test_data', r'pvprognose.json'))
        # PVforecast = PVForecast(prediction_hours = self.prediction_hours, url=pv_forecast_url)
        # #print("PVPOWER",parameter['pvpowernow'])
        # if isfloat(parameter['pvpowernow']):
            # PVforecast.update_ac_power_measurement(date_time=datetime.now(), ac_power_measurement=float(parameter['pvpowernow']))
            # #PVforecast.print_ac_power_and_measurement()
        pv_forecast = parameter['pv_forecast'] #PVforecast.get_pv_forecast_for_date_range(date_now,date) #get_forecast_for_date(date)
        temperaturee_forecast = parameter['temperaturee_forecast'] #PVforecast.get_temperaturee_for_date_range(date_now,date)


        ###############
        # electricity_prices   
        ###############
        specific_date_prices = parameter["electricity_price_euro_per_wh"]
        print(specific_date_prices)
        #print("https://api.batterydoktor.net/prices?start="+date_now+"&end="+date)


        wr = inverter(10000, battery)

        ems = EnergieManagementSystem(total_load = parameter["total_load"], pv_forecast_wh=pv_forecast, electricity_price_euro_per_wh=specific_date_prices, feed_in_tariff_euro_per_wh
=feed_in_tariff_euro_per_wh
, bev=bev, household_appliance=dishwasher,inverter=wr)
        o = ems.simulate(start_hour)
    
        ###############
        # Optimizer Init
        ##############
        opti_param = {}
        opti_param["household_appliances"] = 0
        if dishwasher != None:
                opti_param["household_appliances"] = 1
                
        self.setup_deap_environment(opti_param, start_hour)

        def evaluate_wrapper(individual):
            return self.evaluate(individual, ems, parameter,start_hour,worst_case)
        
        self.toolbox.register("evaluate", evaluate_wrapper)
        start_solution, extra_data = self.optimize(start_params)
        best_solution = start_solution
        o = self.evaluate_inner(best_solution, ems,start_hour)
        bev = ems.bev.to_dict()
        spuelstart_int = None
        discharge_hours_bin, bevcharge_hours_float, spuelstart_int = self.split_individual(best_solution)     
        
     
        print(parameter)
        print(best_solution)
        render_results(parameter["total_load"], pv_forecast, specific_date_prices, o,discharge_hours_bin,bevcharge_hours_float , temperaturee_forecast, start_hour, self.prediction_hours,feed_in_tariff_euro_per_wh
,extra_data=extra_data)
        os.system("cp rendered_results.pdf ~/")
        
           # 'own_consumption_Wh_per_hour': own_consumption_wh_per_hour,
            # 'feed_in_wh_per_hour': feed_in_wh_per_hour,
            # 'grid_consumption_wh_per_hour': grid_consumption_wh_per_hour,
            # 'cost_euro_per_hour': cost_euro_per_hour,
            # 'battery_soc_per_hour': battery_soc_per_hour,
            # 'earnings_euro_per_hour': earnings_euro_per_hour,
            # 'overall_balance_Euro': gesamtkosten_euro,
            # 'E-Auto_SoC_per_hour':bev_soc_per_hour,
            # 'Gesamteinnahmen_Euro': sum(earnings_euro_per_hour),
            # 'Gesamtkosten_Euro': sum(cost_euro_per_hour),
            # "losses_per_hour":losses_wh_per_hour,
            # "Gesamt_losses":sum(losses_wh_per_hour),
            # "household_appliance_wh_per_hour":household_appliance_wh_per_hour        
        
        #print(bev)
        return {"discharge_hours_bin":discharge_hours_bin, "bevcharge_hours_float":bevcharge_hours_float ,"result":o ,"bev_obj":bev,"start_solution":best_solution,"spuelstart":spuelstart_int,"simulation_data":o}





