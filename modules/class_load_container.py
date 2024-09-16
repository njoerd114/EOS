import json
from datetime import datetime, timedelta, timezone
import numpy as np
from pprint import pprint

class total_load:
    def __init__(self, prediction_hours=24):
        self.loads = {}  # Enthält Namen und loads-Arrays für verschiedene Quellen
        self.prediction_hours=prediction_hours
        
    def add(self, name, load_array):
        """
        Fügt ein Array von loads für eine bestimmte Quelle hinzu.
        
        :param name: Name der loadquelle (z.B. "Haushalt", "Wärmepumpe")
        :param load_array: Array von loads, wobei jeder Eintrag einer hour entspricht
        """
        if(len(load_array) != self.prediction_hours):
                raise ValueError(f"total_load Inkonsistente Längen bei den Arrays: ", name," ", len(load_array)  ) 
        self.loads[name] = load_array
    
    
    def calculate_total_load(self):
        """
        Berechnet die gesamte load für jede hour und gibt ein Array der total_loads zurück.
        
        :return: Array der total_loads, wobei jeder Eintrag einer hour entspricht
        """
        if not self.loads:
            return []
        
        # Annahme: Alle loads-Arrays haben die gleiche Länge
        hours = len(next(iter(self.loads.values())))
        total_load_array = [0] * hours
        for load_array in self.loads.values():
            
            total_load_array = [total_load + hoursload for total_load, hoursload in zip(total_load_array, load_array)]
        
        return np.array(total_load_array)
