import numpy as np

class household_appliance:
    def __init__(self, hours=None, consumption_kwh=None, duration_h=None):
        self.hours = hours  # Gesamtzeitraum, für den die Planung erfolgt
        self.consumption_kwh = consumption_kwh  # Gesamtenergieconsumption des Geräts in kWh
        self.duration_h = duration_h  # duration der Nutzung in hours
        self.load_curve = np.zeros(self.hours)  # Initialisiere die load_curve mit Nullen

    def set_start_time(self, start_hour,global_start_hour=0):
        """
        Setzt den Startzeitpunkt des Geräts und generiert eine entsprechende load_curve.
        :param start_hour: Die hour, zu der das Gerät starten soll.
        """
        self.reset()
        # Überprüfe, ob die duration der Nutzung innerhalb des verfügbaren Zeitraums liegt
        if start_hour + self.duration_h > self.hours:
            raise ValueError("Die usage duration überschreitet den verfügbaren Zeitraum.")
        if start_hour < global_start_hour:
            raise ValueError("Die usage duration unterschreitet den verfügbaren Zeitraum.")
        
        # Berechne die power pro hour basierend auf dem Gesamtconsumption und der duration
        power_per_hour = (self.consumption_kwh / self.duration_h) # Umwandlung in Watthour
        #print(start_hour," ",power_per_hour)
        # Setze die power für die duration der Nutzung im load_curven-Array
        self.load_curve[start_hour:start_hour + self.duration_h] = power_per_hour

    def reset(self):
        """
        Setzt die load_curve zurück.
        """
        self.load_curve = np.zeros(self.hours)

    def get_load_curve(self):
        """
        Gibt die aktuelle load_curve zurück.
        """
        return self.load_curve

    def get_load_for_hour(self, hour):
        """
        Gibt die load für eine spezifische hour zurück.
        :param hour: Die hour, für die die load abgefragt wird.
        :return: Die load in Watt für die angegebene hour.
        """
        if hour < 0 or hour >= self.hours:
            raise ValueError("Angegebene hour liegt außerhalb des verfügbaren Zeitraums.")
        
        return self.load_curve[hour]

    def latest_start(self):
        """
        Gibt den spätestmöglichen Startzeitpunkt zurück, an dem das Gerät noch vollständig laufen kann.
        """
        return self.hours - self.duration_h


