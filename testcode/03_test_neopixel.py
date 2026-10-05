# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import neopixel_spi as neopixel

NUM_PIXELS = 72
PIXEL_ORDER = neopixel.GRB
COLORS = (0xFF0000, 0x00FF00, 0x0000FF)
DELAY = 0.1

spi = board.SPI()

pixels = neopixel.NeoPixel_SPI(
    spi, NUM_PIXELS, pixel_order=PIXEL_ORDER, auto_write=False, brightness=0.3
)

def bereken_aantal_leds(waarde: float, waarde_max: float) -> int:
    aantal_leds = int(round((waarde / waarde_max) * 24, 0))
    return aantal_leds
    

def set_color(color1: int, ncolor1: int, color2: int, ncolor2: int, color3: int, ncolor3: int) -> None:
    if ncolor1 > 24:
        ncolor1 = 24
    if ncolor1 < 0:
        ncolor1 = 0

    if ncolor2 > 24:
        ncolor2 = 24
    if ncolor2 < 0:
        ncolor2 = 0

    if ncolor3 > 24:
        ncolor3 = 24
    if ncolor3 < 0:
        ncolor3 = 0
    
    # Add offset for every ring to start at the right point
    # RING 1: 0-23
    # RING 2: 24-47
    # RING 3: 48-71
    if (color1 != None):
        for i in range(ncolor1):
            pixels[0 + i] = color1  # +0 offset
            
            
    if (color2 != None):
        for i in range(ncolor2):
            pixels[24 + i] = color2  # +24 offset
            
            
    if (color3 != None):
        for i in range(ncolor3):
            pixels[48 + i] = color3  # +48 offset
    
    pixels.show()

    

while True:
    # set_color(0x000000, 0, 24)
    # set_color(0xFF0000, 2, 12)
    # time.sleep(5)
    
    sensorwaarde1 = 500
    sensorwaarde1_max = 2000
    
    sensorwaarde2 = 20
    sensorwaarde2_max = 35
    
    sensorwaarde3 = 2.5
    sensorwaarde3_max = 2
    
    aantal_leds_sensor_1 = bereken_aantal_leds(sensorwaarde1, sensorwaarde1_max)
    aantal_leds_sensor_2 = bereken_aantal_leds(sensorwaarde2, sensorwaarde2_max)
    aantal_leds_sensor_3 = bereken_aantal_leds(sensorwaarde3, sensorwaarde3_max)
    
    print(f"Sensor 1 LEDs: {aantal_leds_sensor_1}")
    print(f"Sensor 2 LEDs: {aantal_leds_sensor_2}")
    print(f"Sensor 3 LEDs: {aantal_leds_sensor_3}")
    
    
    sens1_color = 0xFF0000
    sens2_color = 0x00FF00
    sens3_color = 0x0000FF
    
    set_color(sens1_color, aantal_leds_sensor_1, sens2_color, aantal_leds_sensor_2, sens3_color, aantal_leds_sensor_3)
    time.sleep(5)
    
    
    set_color(0x000000, 24,  0x000000,24, 0x000000, 24)
    time.sleep(5)
    # for color in COLORS:
    #     for i in range(NUM_PIXELS):
    #         pixels[i] = color
    #         pixels.show()
    #         time.sleep(DELAY)
    #         pixels.fill(0)