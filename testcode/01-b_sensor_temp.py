# /sys/bus/w1/devices/28-00000fece3cc
# cat w1_slave

# 99 01 4b 46 7f ff 07 10 79 : crc=79 YES
# 99 01 4b 46 7f ff 07 10 79 t=25562

import RPi.GPIO as GPIO
import time
from models.models_sens import OneWire

GPIO.setmode(GPIO.BCM)

base_dir = '/sys/bus/w1/devices/'

onewire = OneWire()

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
        
        temperatuur = onewire.get_temp(path_to_w1_slave)
        print(f"De temperatuur is: {temperatuur} °C")
        
        time.sleep(2)
        
        teller+=1
        

except KeyboardInterrupt:
    print("\nProgramma gestopt door toetsenbord! (ctrl+C)")
    
finally:
    GPIO.cleanup()
