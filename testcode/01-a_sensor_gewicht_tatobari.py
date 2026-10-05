import RPi.GPIO as GPIO
import time
from models.models_sens import HX_Gewicht

# Gebruik BCM pin-nummering
GPIO.setmode(GPIO.BCM)

# Definieer de pinnen
DT_PIN = 5
SCK_PIN = 6
# 21245 / 1036 = 20.5068
kalibratiefactor = 20.50675676  # Standaard 1 voor ruwe data
hx = HX_Gewicht(DT_PIN, SCK_PIN, kalibratiefactor)

try:
    while True:
        # get_weight() berekent direct (Meting - Tare) / Kalibratiefactor
        # De '5' betekent dat hij 5 metingen gemiddeld voor een stabiel getal
        gewicht = round(hx.get_weight(5), 3)
        
        # Kleine truc uit de library om de chip stabiel en wakker te houden
        hx.power_down_up()
        
        print(f"Gewicht: {gewicht} g")
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nProgramma gestopt door toetsenbord! (ctrl+C)")
    
finally:
    GPIO.cleanup()