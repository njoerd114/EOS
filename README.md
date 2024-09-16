# Energiesystem Simulation und optimization

Dieses Projekt bietet eine umfassende Lösung zur Simulation und optimization eines Energiesystems, das auf erneuerbaren Energiequellen basiert. Mit Fokus auf Photovoltaik (PV)-Anlagen, Batteriespeichern (batterys), loadmanagement (consumptioneranforderungen), Wärmepumpen, Elektrofahrzeugen und der Berücksichtigung von electricity_pricedaten ermöglicht dieses System die Vorhersage und optimization des Energieflusses und der Kosten über einen bestimmten Zeitraum.

## Diskussionen und Zugriffsanfragen 
https://www.batterydoktor.net/forum/diy-energie-optimizationssystem-opensource-projekt/

## Todo
- `Backend:` Mehr optimizationsparameter
- `Frontend:` User Management
- `Frontend:` Grafische Ausgabe
- `Frontend:` Speichern von User Einstellungen (PV Anlage usw.)
- `Frontend:` Festeingestellte E-Autos / Wärmepumpen in DB
- `Simulation:` Wärmepumpe allgemeineren Ansatz
- `Simulation:` electricity_pricevorhersage > 1D (Timeseries Forecast)
- `Simulation:` loadverteilung 1h Werte -> Minuten (Tabelle) 
- `Dynamische loads:` z.B. eine Spülmaschine, welche gesteuert werdeb jabb,
- `Simulation:` AC Chargen möglich
- `optimization:` E-Auto battery voll = in der 0/1 Liste keine Möglichkeit mehr auf 1 (aktuell ist der optimization das egalm ändert ja nichts) optimizationsparameter reduzieren
- `Backend:` Visual Cleaner (z.B. E-Auto battery = 100%, dann sollte die Lademöglichkeit auf 0 stehen. Zumindest bei der Ausgabe sollte das "sauber" sein)
- `Backend:` Cache regelmäßig leeren können (API)

## Installation

Gute Install Anleitung: 
https://meintechblog.de/2024/09/05/andreas-schmitz-joerg-installiert-mein-energieoptimizationssystem/

Das Projekt erfordert Python 3.8 oder neuer.

### Schnellanleitung

Unter Linux (Ubuntu/Debian):

```bash
sudo apt install make
```

Unter Macos (benötigt [Homebrew](https://brew.sh)):

```zsh
brew install make
```

Nun `config.example.py` anpassen und dann in `config.py` umbennenen. Anschließend kann der Server über `make run` gestartet werden.
Eine vollständige Übersicht über die wichtigsten Kurzbefehle gibt `make help`.

### Ausführliche Anleitung

Alle notwendigen Abhängigkeiten können über `pip` installiert werden. Klonen Sie das Repository und installieren Sie die erforderlichen Pakete mit:

```bash
git clone https://github.com/batterydoktor-EOS/EOS
cd EOS
```
Als Nächstes legen wir ein virtuelles Environment an. Es dient zur Ablage der Python-Abhängigkeiten,
die wir später per `pip` installieren:

```bash
virtualenv .venv
```

Schließlich installieren wir die Python-Abhängigkeiten von EOS:

```bash
.venv/bin/pip install -r requirements.txt
```

Um immer die Python-Version aus dem Virtual-Env zu verwenden, sollte vor der Arbeit in
EOS Folgendes aufgerufen werden:

```bash
source .venv/bin/activate
```

(für Bash-Nutzende, der Standard unter Linux) oder

```zsh
. .venv/bin/activate
```

(wenn zsh verwendet wird, vor allem MacOS-Nutzende).

Sollte `pip install` die mariadb-Abhängigkeit nicht installieren können,
dann helfen folgende Kommandos:

* Debian/Ubuntu: `sudo apt-get install -y libmariadb-dev`
* Macos/Homebrew: `brew install mariadb-connector-c`

gefolgt von einem erneuten `pip install -r requirements.txt`.

## Nutzung

`config.example.py` anpassen und dann in config.py umbennenen
Um das System zu nutzen, führen Sie `flask_server.py` aus, damit wird der Server gestartet


```bash
./flask_server.py
```
## Klassen und Funktionalitäten

In diesem Projekt werden verschiedene Klassen verwendet, um die Komponenten eines Energiesystems zu simulaten und zu optimieren. Jede Klasse repräsentiert einen spezifischen Aspekt des Systems, wie afterfolgend beschrieben:

- `PVbattery`: Simuliert einen Batteriespeicher, einschließlich der Kapazität, des charge_levels und jetzt auch der Lade- und Entladelosses.

- `PVForecast`: Stellt Vorhersagedaten für die Photovoltaik-generation bereit, basierend auf Wetterdaten und historischen generationsdaten.

- `Load`: Modelliert die loadanforderungen des Haushalts oder Unternehmens, ermöglicht die Vorhersage des zukünftigen Energiebedarfs.

- `HeatPump`: Simuliert eine Wärmepumpe, einschließlich ihres Energieconsumptions und ihrer Effizienz unter verschiedenen Betriebsbedingungen.

- `electricity_price`: Bietet Informationen zu den electricity_pricesn, ermöglicht die optimization des Energieconsumptions und der -generation basierend auf Tarifinformationen.

- `EMS`: Das Energiemanagementsystem (EMS) koordiniert die Interaktion zwischen den verschiedenen Komponenten, führt die optimization durch und simuliert den Betrieb des gesamten Energiesystems.

Diese Klassen arbeiten zusammen, um eine detaillierte Simulation und optimization des Energiesystems zu ermöglichen. Für jede Klasse können spezifische Parameter und Einstellungen angepasst werden, um verschiedene Szenarien und Strategien zu testen.

### Anpassung und Erweiterung

Jede Klasse ist so gestaltet, dass sie leicht angepasst und erweitert werden kann, um zusätzliche Funktionen oder Verbesserungen zu integrieren. Beispielsweise können neue Methoden zur genaueren Modellierung des Verhaltens von PV-Anlagen oder Batteriespeichern hinzugefügt werden. Entwickler sind eingeladen, das System after ihren Bedürfnissen zu modifizieren und zu erweitern.


# Input für den Flask Server (Stand 30.07.204)
Beschreibt die Struktur und Datentypen des JSON-Objekts, das an den Flask-Server gesendet wird. Hier mit einem Prognosezeitraum von 48 hours!

## Felder des JSON-Objekts

### electricity_price_euro_per_wh
- **Beschreibung**: Ein Array von Floats, das den electricity_price in Euro pro Watthour für verschiedene Zeitintervalle darstellt.
- **Typ**: Array
- **Element-Typ**: Float
- **Länge**: 48  

### total_load
- **Beschreibung**: Ein Array von Floats, das die total_load (consumption) in Watt für verschiedene Zeitintervalle darstellt.
- **Typ**: Array
- **Element-Typ**: Float
- **Länge**: 48

### pv_forecast
- **Beschreibung**: Ein Array von Floats, das die prognostizierte Photovoltaik-power in Watt für verschiedene Zeitintervalle darstellt.
- **Typ**: Array
- **Element-Typ**: Float
- **Länge**: 48

### temperaturee_forecast
- **Beschreibung**: Ein Array von Floats, das die temperaturevorhersage in Grad Celsius für verschiedene Zeitintervalle darstellt.
- **Typ**: Array
- **Element-Typ**: Float
- **Länge**: 48

### pv_soc
- **Beschreibung**: Ein Integer, der den charge_level des PV batterys zum START der aktuellen hour anzeigt, das ist nicht der aktuelle!!! 
- **Typ**: Integer

### pv_battery_cap
- **Beschreibung**: Ein Integer, der die Kapazität des Photovoltaik-batterys in Watthours darstellt.
- **Typ**: Integer

### feed_in_tariff_euro_per_wh

- **Beschreibung**: Ein Float, der die Einspeisevergütung in Euro pro Watthour darstellt.
- **Typ**: Float

### bev_min_soc
- **Beschreibung**: Ein Integer, der den minimalen charge_level (State of Charge) des Elektroautos in Prozent darstellt.
- **Typ**: Integer

### bev_cap
- **Beschreibung**: Ein Integer, der die Kapazität des Elektroauto-batterys in Watthours darstellt.
- **Typ**: Integer

### bev_charge_efficiency
- **Beschreibung**: Ein Float, der die Ladeeffizienz des Elektroautos darstellt.
- **Typ**: Float

### bev_charge_power
- **Beschreibung**: Ein Integer, der die charging_power des Elektroautos in Watt darstellt.
- **Typ**: Integer

### bev_soc
- **Beschreibung**: Ein Integer, der den aktuellen charge_level (State of Charge) des Elektroautos in Prozent darstellt.
- **Typ**: Integer

### start_solution
- **Beschreibung**: Kann null sein oder eine vorherige Lösung enthalten (wenn vorhanden).
- **Typ**: null oder object

### household_appliance_wh
- **Beschreibung**: Ein Integer, der den Energieconsumption eines Haushaltsgeräts in Watthours darstellt.
- **Typ**: Integer

### household_appliance_duration
- **Beschreibung**: Ein Integer, der die duration der Nutzung des Haushaltsgeräts in hours darstellt.
- **Typ**: Integer







# JSON-Output Beschreibung

Dieses Dokument beschreibt die Struktur und Datentypen des JSON-Outputs, den der Flask-Server zurückgibt. Hier mit einem Prognosezeitraum von 48h

## Felder des JSON-Outputs (Stand 30.7.2024)

### discharge_hours_bin
- **Beschreibung**: Ein Array von Binärwerten (0 oder 1), das anzeigt, ob in einer bestimmten hour Energie entladen wird.
- **Typ**: Array
- **Element-Typ**: Integer (0 oder 1)
- **Länge**: 48

### bev_obj
- **Beschreibung**: Ein Objekt, das Informationen über das Elektroauto enthält.
  - **charge_array**: Ein Array von Binärwerten (0 oder 1), das anzeigt, ob das Elektroauto in einer bestimmten hour geladen wird.
    - **Typ**: Array
    - **Element-Typ**: Integer (0 oder 1)
    - **Länge**: 48
  - **discharge_array**: Ein Array von Binärwerten (0 oder 1), das anzeigt, ob das Elektroauto in einer bestimmten hour entladen wird.
    - **Typ**: Array
    - **Element-Typ**: Integer (0 oder 1)
    - **Länge**: 48
  - **discharging_efficiency**: Die Entladeeffizienz des Elektroautos.
    - **Typ**: Float
  - **hours**: Die Anzahl der hours, für die die Simulation durchgeführt wird.
    - **Typ**: Integer
  - **capacity_wh**: Die Kapazität des Elektroauto-batterys in Watthours.
    - **Typ**: Integer
  - **charging_efficiency**: Die Ladeeffizienz des Elektroautos.
    - **Typ**: Float
  - **max_charging_power_w**: Die maximale charging_power des Elektroautos in Watt.
    - **Typ**: Integer
  - **soc_wh**: Der charge_level (State of Charge) des Elektroautos in Watthours.
    - **Typ**: Integer
  - **initial_soc_percentage**: Der initiale charge_level (State of Charge) des Elektroautos in Prozent.
    - **Typ**: Integer

### bevcharge_hours_float
- **Beschreibung**: Ein Array von Binärwerten (0 oder 1), das anzeigt, ob das Elektroauto in einer bestimmten hour geladen wird.
- **Typ**: Array
- **Element-Typ**: Integer (0 oder 1)
- **Länge**: 48

### result
- **Beschreibung**: Ein Objekt, das die results der Simulation enthält.
  - **E-Auto_SoC_per_hour**: Ein Array von Floats, das den charge_level des Elektroautos für jede hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **own_consumption_Wh_per_hour**: Ein Array von Floats, das den own_consumption in Watthours pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **earnings_euro_per_hour**: Ein Array von Floats, das die Einnahmen in Euro pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **Gesamt_losses**: Die gesamten losses in Watthours.
    - **Typ**: Float
  - **overall_balance_Euro**: Die gesamte balance in Euro.
    - **Typ**: Float
  - **Gesamteinnahmen_Euro**: Die gesamten Einnahmen in Euro.
    - **Typ**: Float
  - **Gesamtkosten_Euro**: Die gesamten Kosten in Euro.
    - **Typ**: Float
  - **household_appliance_wh_per_hour**: Ein Array von Floats, das den Energieconsumption eines Haushaltsgeräts in Watthours pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **cost_euro_per_hour**: Ein Array von Floats, das die Kosten in Euro pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **grid_consumption_wh_per_hour**: Ein Array von Floats, das den grid_consumption in Watthours pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **feed_in_wh_per_hour**: Ein Array von Floats, das die grid_feed_in in Watthours pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **losses_per_hour**: Ein Array von Floats, das die losses pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **battery_soc_per_hour**: Ein Array von Floats, das den charge_level des batterys in Prozent pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35

### simulation_data
- **Beschreibung**: Ein Objekt, das die simulierten Daten enthält.
  - **E-Auto_SoC_per_hour**: Ein Array von Floats, das den simulierten charge_level des Elektroautos pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **own_consumption_Wh_per_hour**: Ein Array von Floats, das den simulierten own_consumption in Watthours pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **earnings_euro_per_hour**: Ein Array von Floats, das die simulierten Einnahmen in Euro pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **Gesamt_losses**: Die gesamten simulierten losses in Watthours.
    - **Typ**: Float
  - **overall_balance_Euro**: Die gesamte simulierte balance in Euro.
    - **Typ**: Float
  - **Gesamteinnahmen_Euro**: Die gesamten simulierten Einnahmen in Euro.
    - **Typ**: Float
  - **Gesamtkosten_Euro**: Die gesamten simulierten Kosten in Euro.
    - **Typ**: Float
  - **household_appliance_wh_per_hour**: Ein Array von Floats, das den simulierten Energieconsumption eines Haushaltsgeräts in Watthours pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **cost_euro_per_hour**: Ein Array von Floats, das die simulierten Kosten in Euro pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **grid_consumption_wh_per_hour**: Ein Array von Floats, das den simulierten grid_consumption in Watthours pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **feed_in_wh_per_hour**: Ein Array von Floats, das die simulierte grid_feed_in in Watthours pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **losses_per_hour**: Ein Array von Floats, das die simulierten losses pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35
  - **battery_soc_per_hour**: Ein Array von Floats, das den simulierten charge_level des batterys in Prozent pro hour darstellt.
    - **Typ**: Array
    - **Element-Typ**: Float
    - **Länge**: 35

### spuelstart
- **Beschreibung**: Kann `null` sein oder ein Objekt enthalten, das den Spülstart darstellt (wenn vorhanden).
- **Typ**: null oder object

### start_solution
- **Beschreibung**: Ein Array von Binärwerten (0 oder 1), das eine mögliche Startlösung für die Simulation darstellt.
- **Typ**: Array
- **Element-Typ**: Integer (0 oder 1)
- **Länge**: 48
