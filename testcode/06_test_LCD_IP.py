import RPi.GPIO as GPIO
import time
from subprocess import check_output
from models.models_sens import HX_Gewicht, OneWire, Mcp_Druk, LED_Rings_3, Lcd_i2c

import board
import neopixel_spi as neopixel

lcd = Lcd_i2c(0x38, 17, 27)

def get_rpi_ip() -> list[str]:
    # bytes ophalen, omzetten naar tekst (decode)
    # \n weghalen (strip)
    ips = check_output(["hostname", "--all-ip-addresses"]).decode("utf8").strip()
    print(ips)
    
    # Opsplitsen in een list
    ips = ips.split(" ")
    return ips

try:
    while True:
        ips = get_rpi_ip()
        eth0_ip = ips[0]
        wlan0_ip = ips[1]
        print(f"\neth0: {eth0_ip}")
        print(f"wlan0: {wlan0_ip}")
        
        lcd.send_instruction(0x80 | 0x00)
        lcd.write_message(f"{eth0_ip:<16}")
        lcd.send_instruction(0x80 | 0x40)
        lcd.write_message(f"{wlan0_ip:<16}")
        time.sleep(10)


except KeyboardInterrupt:
    print("\nProgramma gestopt door toetsenbord! (ctrl+C)")
    
finally:
    lcd.close_i2c()
    GPIO.cleanup()
