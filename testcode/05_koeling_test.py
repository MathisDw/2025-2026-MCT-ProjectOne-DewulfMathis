import RPi.GPIO as GPIO
import time
from models.models_sens import HX_Gewicht, OneWire, Mcp_Druk, LED_Rings_3

import board
import neopixel_spi as neopixel


GPIO.setmode(GPIO.BCM)
koeling = 26

GPIO.setup(koeling, GPIO.OUT)

try:
    while True:
        print("hallo")
        GPIO.output(koeling, GPIO.HIGH)
        time.sleep(5)
        GPIO.output(koeling, GPIO.LOW)
        time.sleep(2)
        

except KeyboardInterrupt:
    print("\nProgramma gestopt door toetsenbord! (ctrl+C)")
    
finally:
    GPIO.cleanup()

