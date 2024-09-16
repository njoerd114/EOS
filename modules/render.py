import numpy as np
from modules.class_summertime import *
from modules.class_load_container import total_load  # Stellen Sie sicher, dass dies dem tatsächlichen Importpfad entspricht
import matplotlib
matplotlib.use('Agg')  # Setzt das Backend auf Agg

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime


def render_results(total_load, pv_forecast, electricity_prices, results,  discharge_hours, charging_possible, temperaturee, start_hour, prediction_hours,feed_in_tariff_euro_per_wh
, filename="rendered_results.pdf", extra_data=None):

    #####################
    # 24h 
    #####################
    with PdfPages(filename) as pdf:

        
        # load und PV-generation
        plt.figure(figsize=(14, 14))
        plt.subplot(3, 3, 1)
        hours = np.arange(0, prediction_hours)
        
        total_load_array = np.array(total_load)
        # Einzelloads plotten
        #for name, load_array in total_load.loads.items():
        plt.plot(hours, total_load_array, label=f'load (Wh)', marker='o')
        
        # total_load berechnen und plotten
        total_load_array = np.array(total_load)
        plt.plot(hours, total_load_array, label='total_load (Wh)', marker='o', linewidth=2, linestyle='--')
        plt.xlabel('hour')
        plt.ylabel('load (Wh)')
        plt.title('loadprofile')
        plt.grid(True)
        plt.legend()


        # electricity_prices
        hoursp = np.arange(0, len(electricity_prices))
        plt.subplot(3, 2, 2)
        plt.plot(hoursp, electricity_prices, label='electricity_price (€/Wh)', color='purple', marker='s')
        plt.title('electricity_prices')
        plt.xlabel('hour des Tages')
        plt.ylabel('Preis (€/Wh)')
        plt.legend()
        plt.grid(True)

        # electricity_prices
        hoursp = np.arange(1, len(electricity_prices)+1)
        plt.subplot(3, 2, 3)
        plt.plot(hours, pv_forecast, label='PV-generation (Wh)', marker='x')
        plt.title('PV Forecast')
        plt.xlabel('hour des Tages')
        plt.ylabel('Wh')
        plt.legend()
        plt.grid(True)

        # Vergütung
        hoursp = np.arange(0, len(electricity_prices))
        plt.subplot(3, 2, 4)
        plt.plot(hours, feed_in_tariff_euro_per_wh
, label='Vergütung €/Wh', marker='x')
        plt.title('Vergütung')
        plt.xlabel('hour des Tages')
        plt.ylabel('€/Wh')
        plt.legend()
        plt.grid(True)


        # temperature Forecast
        plt.subplot(3, 2, 5)
        plt.title('temperature Forecast °C')
        plt.plot(hours, temperaturee, label='temperature °C', marker='x')
        plt.xlabel('hour des Tages')
        plt.ylabel('°C')
        plt.legend()
        plt.grid(True)

        pdf.savefig()  # Speichert den aktuellen Figure-State im PDF
        plt.close()  # Schließt die aktuelle Figure, um Speicher freizugeben


        #####################
        # Start_Hour  
        #####################    
        
        plt.figure(figsize=(14, 10))
        
        if is_dst_change(datetime.now()):
                hours = np.arange(start_hour, prediction_hours-1)
        else:
                hours = np.arange(start_hour, prediction_hours)
        
        # print(is_dst_change(datetime.now())," ",datetime.now())
        # print(start_hour," ",prediction_hours," ",hours)
        # print(results['own_consumption_Wh_per_hour'])
        # own_consumption, grid_feed_in und grid_consumption
        plt.subplot(3, 2, 1)
        plt.plot(hours, results['load_wh_per_hour'], label='load (Wh)', marker='o')
        plt.plot(hours, results['household_appliance_wh_per_hour'], label='Haushaltsgerät (Wh)', marker='o')
        plt.plot(hours, results['feed_in_wh_per_hour'], label='grid_feed_in (Wh)', marker='x')
        plt.plot(hours, results['grid_consumption_wh_per_hour'], label='grid_consumption (Wh)', marker='^')
        plt.plot(hours, results['losses_per_hour'], label='losses (Wh)', marker='^')
        plt.title('Energiefluss pro hour')
        plt.xlabel('hour')
        plt.ylabel('Energie (Wh)')
        plt.legend()
        
        
        
        
        plt.subplot(3, 2, 2)
        plt.plot(hours, results['battery_soc_per_hour'], label='PV battery (%)', marker='x')
        plt.plot(hours, results['E-Auto_SoC_per_hour'], label='E-Auto battery (%)', marker='x')
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))  # Legende außerhalb des Plots platzieren
        plt.grid(True, which='both', axis='x')  # Grid für jede hour

        ax1 = plt.subplot(3, 2, 3)
        for hour, value in enumerate(discharge_hours):
            #if value == 1:
            print(hour)
            ax1.axvspan(hour, hour+1, color='red',ymax=value, alpha=0.3, label='Entlademöglichkeit' if hour == 0 else "")
        for hour, value in enumerate(charging_possible):
            #if value == 1:
            ax1.axvspan(hour, hour+1, color='green',ymax=value, alpha=0.3, label='Lademöglichkeit' if hour == 0 else "")
        ax1.legend(loc='upper left')
        ax1.set_xlim(0, prediction_hours)  

        pdf.savefig()  # Speichert den aktuellen Figure-State im PDF
        plt.close()  # Schließt die aktuelle Figure, um Speicher freizugeben
        
        
        
        
        
        
        
        plt.grid(True)
        fig, axs = plt.subplots(1, 2, figsize=(14, 10))  # Erstellt 1x2 Raster von Subplots
        gesamtkosten = results['Gesamtkosten_Euro']
        gesamteinnahmen = results['Gesamteinnahmen_Euro']
        overall_balance = results['overall_balance_Euro']
        losses = results['Gesamt_losses']

        # Kosten und Einnahmen pro hour auf der ersten Achse (axs[0])
        axs[0].plot(hours, results['cost_euro_per_hour'], label='Kosten (Euro)', marker='o', color='red')
        axs[0].plot(hours, results['earnings_euro_per_hour'], label='Einnahmen (Euro)', marker='x', color='green')
        axs[0].set_title('Finanzielle balance pro hour')
        axs[0].set_xlabel('hour')
        axs[0].set_ylabel('Euro')
        axs[0].legend()
        axs[0].grid(True)

        # Zusammenfassende Finanzen auf der zweiten Achse (axs[1])
        labels = ['GesamtKosten [€]', 'GesamtEinnahmen [€]', 'overall_balance [€]']
        werte = [gesamtkosten, gesamteinnahmen, overall_balance]
        colors = ['red' if wert > 0 else 'green' for wert in werte]
        axs[1].bar(labels, werte, color=colors)
        axs[1].set_title('Finanzübersicht')
        axs[1].set_ylabel('Euro')

        # Zweite Achse (ax2) für die losses, geteilt mit axs[1]
        ax2 = axs[1].twinx()
        ax2.bar('Gesamtlosses', losses, color='blue')
        ax2.set_ylabel('losses [Wh]', color='blue')
        ax2.tick_params(axis='y', labelcolor='blue')

        pdf.savefig()  # Speichert die komplette Figure im PDF
        plt.close()  # Schließt die Figure
        
        

        if extra_data != None:
                plt.figure(figsize=(14, 10))
                plt.subplot(1, 2, 1)
                f1 = np.array(extra_data["losses"])
                f2 = np.array(extra_data["balance"])
                n1 = np.array(extra_data["side_condition"])
                scatter = plt.scatter(f1, f2, c=n1, cmap='viridis')

                # Farblegende hinzufügen
                plt.colorbar(scatter, label='side_condition')

                pdf.savefig()  # Speichert die komplette Figure im PDF
                plt.close()  # Schließt die Figure

                
                plt.figure(figsize=(14, 10))
                filtered_losses = np.array([v for v, n in zip(extra_data["losses"], extra_data["side_condition"]) if n < 0.01])
                filtered_balance = np.array([b for b, n in zip(extra_data["balance"], extra_data["side_condition"]) if n< 0.01])
                
                beste_losses = min(filtered_losses)
                schlechteste_losses = max(filtered_losses)
                beste_balance = min(filtered_balance)
                schlechteste_balance = max(filtered_balance)

                data = [filtered_losses, filtered_balance]
                labels = ['losses', 'balance']
                # Plot-Erstellung
                fig, axs = plt.subplots(1, 2, figsize=(10, 6), sharey=False)  # Zwei Subplots, getrennte y-Achsen

                # Erster Boxplot für losses
                #axs[0].boxplot(data[0])
                axs[0].violinplot(data[0],
                          showmeans=True,
                          showmedians=True)
                axs[0].set_title('losses')
                axs[0].set_xticklabels(['losses'])

                # Zweiter Boxplot für balance
                axs[1].violinplot(data[1],
                          showmeans=True,
                          showmedians=True)
                axs[1].set_title('balance')
                axs[1].set_xticklabels(['balance'])

                # Feinabstimmung
                plt.tight_layout()
        
        
        pdf.savefig()  # Speichert den aktuellen Figure-State im PDF
        plt.close() 
        
        # plt.figure(figsize=(14, 10))
        # # Kosten und Einnahmen pro hour
        # plt.subplot(1, 2, 1)
        # plt.plot(hours, results['cost_euro_per_hour'], label='Kosten (Euro)', marker='o', color='red')
        # plt.plot(hours, results['earnings_euro_per_hour'], label='Einnahmen (Euro)', marker='x', color='green')
        # plt.title('Finanzielle balance pro hour')
        # plt.xlabel('hour')
        # plt.ylabel('Euro')
        # plt.legend()


        # plt.grid(True)
        # #plt.figure(figsize=(14, 10))
        # # Zusammenfassende Finanzen
        # #fig, ax1 = plt.subplot(1, 2, 2)
        # fig, ax1 = plt.subplots()
        # gesamtkosten = results['Gesamtkosten_Euro']
        # gesamteinnahmen = results['Gesamteinnahmen_Euro']
        # overall_balance = results['overall_balance_Euro']
        # labels = ['GesamtKosten [€]', 'GesamtEinnahmen [€]', 'overall_balance [€]']
        # werte = [gesamtkosten, gesamteinnahmen, overall_balance]
        # colors = ['red' if wert > 0 else 'green' for wert in werte]

        # ax1.bar(labels, werte, color=colors)
        # ax1.set_ylabel('Euro')
        # ax1.set_title('Finanzübersicht')

        # # Zweite Achse (ax2) für die losses, geteilt mit ax1
        # ax2 = ax1.twinx()
        # losses = results['Gesamt_losses']
        # ax2.bar('Gesamtlosses', losses, color='blue')
        # ax2.set_ylabel('losses [Wh]', color='blue')

        # # Stellt sicher, dass die Achsenbeschriftungen der zweiten Achse in der gleichen Farbe angezeigt werden
        # ax2.tick_params(axis='y', labelcolor='blue')

        # pdf.savefig()  # Speichert den aktuellen Figure-State im PDF
        # plt.close()  # Schließt die aktuelle Figure, um Speicher freizugeben

        
        # plt.title('Gesamtkosten')
        # plt.ylabel('Euro')


        # plt.legend()
        # plt.grid(True)

        # plt.tight_layout()
        #plt.show()

    

