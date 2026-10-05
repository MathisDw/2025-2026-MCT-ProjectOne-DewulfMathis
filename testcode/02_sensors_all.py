import RPi.GPIO as GPIO
import time
from models.models_sens import HX_Gewicht, OneWire, Mcp_Druk

GPIO.setmode(GPIO.BCM)

DT_PIN = 5
SCK_PIN = 6
# 21245 / 1036 = 20.5068
# Standaard 1 voor ruwe data
kalibratiefactor = 20.50675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675
hx = HX_Gewicht(DT_PIN, SCK_PIN, kalibratiefactor)

onewire = OneWire()
base_dir = '/sys/bus/w1/devices/'

mcp = Mcp_Druk(1, 0)
druksensor = 0

teller = 0

try:
    # Zoek het pad één keer op bij het starten
    path_to_w1_slave = onewire.find_sensor_path()
    
    if path_to_w1_slave is None:
        print("Geen sensor gevonden! Controleer je bedrading en of 1-Wire is ingeschakeld.")
    else:
        print(f"Sensor gevonden op: {path_to_w1_slave}")
    
    while True:
        print(f"\n{teller}-----------------------------------------------")
        # get_weight() berekent direct (Meting - Tare) / Kalibratiefactor
        # De '5' betekent dat hij 5 metingen gemiddeld voor een stabiel getal
        gewicht = round(hx.get_weight(5), 3)
        
        # Kleine truc uit de library om de chip stabiel en wakker te houden
        hx.power_down_up()
        
        print(f"Gewicht: {gewicht} g")
        
        temperatuur = onewire.get_temp(path_to_w1_slave)
        print(f"De temperatuur is: {temperatuur} °C")
        
        waarde = mcp.read_channel(druksensor)
        print(f"waarde MCP: {waarde}")
        
        druk = mcp.get_druk(waarde)
        print(f"Druk = {druk} bar")
        
        time.sleep(0.01)
        
        teller+=1
        

except KeyboardInterrupt:
    print("\nProgramma gestopt door toetsenbord! (ctrl+C)")
    
finally:
    GPIO.cleanup()
    mcp.close_spi()
