import RPi.GPIO as GPIO
import time
from models.models_sens import HX_Gewicht, OneWire, Mcp_Druk, LED_Rings_3

import board
import neopixel_spi as neopixel


GPIO.setmode(GPIO.BCM)

# SENSORS
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

# LED rings
NUM_PIXELS = 72
PIXEL_ORDER = neopixel.GRB
COLORS = (0xFF0000, 0x00FF00, 0x0000FF)
DELAY = 0.1

spi = board.SPI()

pixels = neopixel.NeoPixel_SPI(
    spi, NUM_PIXELS, pixel_order=PIXEL_ORDER, auto_write=False, brightness=0.3
)

# pixels.deinit()


# pixels = neopixel.NeoPixel_SPI(
#     spi, NUM_PIXELS, pixel_order=PIXEL_ORDER, auto_write=False, brightness=0.5
# )


rings = LED_Rings_3(pixels)

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
        
        # LED-ringen aansturen van de sensorwaarden
        gewicht_max = 1000
        temp_max = 30
        druk_max = 2
        
        leds_sens1 = rings.bereken_aantal_leds(gewicht, gewicht_max)
        leds_sens2 = rings.bereken_aantal_leds(temperatuur, temp_max)
        leds_sens3 = rings.bereken_aantal_leds(druk, druk_max)
        
        print(f"Sensor 1 LEDs: {leds_sens1}")
        print(f"Sensor 2 LEDs: {leds_sens2}")
        print(f"Sensor 3 LEDs: {leds_sens3}")
    
        
        color_sens1 = 0xFF0000
        color_sens2 = 0x00FF00
        color_sens3 = 0x0000FF
        
        rings.set_color(color_sens1, leds_sens1, color_sens2, leds_sens2, color_sens3, leds_sens3)
        time.sleep(1)
        
        teller+=1
        

except KeyboardInterrupt:
    print("\nProgramma gestopt door toetsenbord! (ctrl+C)")
    
finally:
    GPIO.cleanup()
    mcp.close_spi()
    rings.pixels.fill(0x000000)
