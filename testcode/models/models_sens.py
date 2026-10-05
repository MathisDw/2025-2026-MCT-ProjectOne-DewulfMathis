from RPi import GPIO
from smbus import SMBus
import spidev
import glob
import time
from models.hx711 import HX711
import neopixel_spi as neopixel

class HX_Gewicht:
    # ctor
    def __init__(self, gpio_DT_pin: int, gpio_SCK_pin: int, par_kalibratiefactor: int=1):
        self.__DT_pin = gpio_DT_pin
        self.__SCK_pin = gpio_SCK_pin
        self.__kalibratiefactor = par_kalibratiefactor
        
        self.__hx = HX711(self.DT_pin, self.SCK_pin)
        self.setup_weegschaal()
    
    # properties
    # ********** property DT_pin - (getter only) ***********
    @property
    def DT_pin(self) -> int:
        """ The DT_pin property. """
        return self.__DT_pin
    
    # ********** property SCK_pin - (getter only) ***********
    @property
    def SCK_pin(self) -> int:
        """ The SCK_pin property. """
        return self.__SCK_pin
    
    # ********** property hx - (getter only) ***********
    @property
    def hx(self) -> HX711:
        """ The hx property. """
        return self.__hx
    
    # ********** property kalibratiefactor - (getter only) ***********
    @property
    def kalibratiefactor(self) -> type:
        """ The kalibratiefactor property. """
        return self.__kalibratiefactor
    
    # extra methods
    def setup_weegschaal(self):
        # Bepaal de bit-volgorde (Standaard vereist door de tatobari library)
        # Most Significant Byte (bij de eerste) en Most Significant Bit (bij de tweede).
        self.hx.set_reading_format("MSB", "MSB")

        # --- KALIBRATIE FACTOR ---
        # Volg *** 1-a_kalibreren.md ***
        # 21245 / 1036 = 20.5068
        # self.kalibratiefactor = 20.50675676  # Standaard 1 voor ruwe data
        self.hx.set_reference_unit(self.kalibratiefactor)

        self.hx.reset()
        
        print("Bezig met tarreren (nulmeting)... Zorg dat de weegschaal leeg is!")
        time.sleep(2)
        
        # Weegschaal tarreren
        self.hx.tare()
        
        print("Tarreren gelukt! Start met wegen.")
        print("----------------------------------")
    
    def get_weight(self, times):
        gewicht = self.hx.get_weight(times)
        return gewicht
        
    def power_down_up(self):
        self.hx.power_down()
        self.hx.power_up()
    def tare(self):
        print("Bezig met tarreren (nulmeting)... Zorg dat de weegschaal leeg is!")
        self.hx.tare()

class OneWire:
    # ctor
    def __init__(self, par_onewire_base_dir: str='/sys/bus/w1/devices/', par_file_index: int=0):
        self.__base_dir = par_onewire_base_dir
        self.__file_index = par_file_index
    
    # properties
    # ********** property base_dir - (getter only) ***********
    @property
    def base_dir(self) -> str:
        """ The base_dir property. """
        return self.__base_dir
    
    # ********** property file_index - (getter only) ***********
    @property
    def file_index(self) -> type:
        """ The file_index property. """
        return self.__file_index
    
    # extra methods
    
    def find_sensor_path(self):
        """Zoekt automatisch naar de aangesloten 1-Wire sensor."""
        try:
            # Zoek naar alle mappen die beginnen met '28-' en pak de eerste [0]
            device_folder = glob.glob(self.base_dir + '28*')[self.file_index]
            device_file = device_folder + '/w1_slave'
            return device_file
        except IndexError:
            # Als de lijst leeg is, is er geen sensor gevonden
            return None

    def __inlezen_file(self, path):
        fo = open(path, "r")
        inhoud = fo.read()
        fo.close()
        return inhoud

    def get_temp(self, path: str) -> float:
        try:
            file = self.__inlezen_file(path)
            pos = file.find('t=')
        
            temp_string = file[pos+2:].strip()

            temperatuur = float(temp_string) / 1000.0
            # print(f"De temperatuur is: {temperatuur}°C")
            return temperatuur
    
        except FileNotFoundError as ex:
            print(f"File niet gevonden: {ex}")
            return None
        except ValueError as ex:
            print(f"Kon temperatuur niet omzetten: {ex}")
            return None

class Mcp:
    # Klasse voor MCP3008
    # ctor
    def __init__(self, par_bus=0, par_device=0):
        self.__bus = par_bus
        self.__device = par_device
        
        self.__spi = spidev.SpiDev()
        self.spi.open(self.bus, self.device) # standard: Bus SPI0, slave op CE 0
        self.spi.max_speed_hz = 10 ** 5 # 100 kHz
    
    # properties
    # ********** property bus - (getter only) ***********
    @property
    def bus(self) -> int:
        """ The bus property. """
        return self.__bus
    
    # ********** property device - (getter only) ***********
    @property
    def device(self) -> int:
        """ The device property. """
        return self.__device
    
    # ********** property spi - (getter only) ***********
    @property
    def spi(self) -> spidev.SpiDev:
        """ The spi property. """
        return self.__spi
    
    # extra methods
    def read_channel(self, channel: int):
        
        # bytes_out --> 3 bytes worden doorgestuurd
        # startbit: 0000 0001,
        # Single ended + Kanaal (bv.1) + 4 bits "Don't care" --> 0: 1001 0000,
        # "Don't care" --> We sturen 0 door
        bytes_out = [1, 0x80 | (channel << 4), 0]
        # print(f"\nbytes_out (channel {channel}): {bytes_out}")
        
        # Stuurt 3 bytes_out door naar de chip
        # Vangt tegelijkertijd het antwoord op
        # antwoord (3 bytes) wordt opgeslagen
        adc_antwoord = self.spi.xfer(bytes_out)
        
        # (adc_antwoord[1] & 3) : Enkel de laatste 2 bits van 2de byte
        # << 8 : bits opschuiven
        # | adc_antwoord[2] : 3de byte toevoegen
        resultaat = (adc_antwoord[1] & 3) << 8 | adc_antwoord[2]
        
        # print(f"\nArray ADC antwoord: {adc_antwoord}")
        # print(f"Resultaat voor channel {channel}: {resultaat}")
        return resultaat
    
    def close_spi(self):
        self.spi.close()

class Mcp_Druk(Mcp):
    # ctor
    def __init__(self, par_bus=0, par_device=0):
        super().__init__(par_bus, par_device)
        
    def get_druk(self, mcp_waarde):
        # Voorkom delen door nul of rare fouten als de sensor los zit
        if mcp_waarde <= 0:
            return 1.0

        # 1. Reken de ruwe waarde om naar Voltage
        voltage = (mcp_waarde / 1023.0) * 3.3

        # 2. De eigenschappen van jouw sensor (VUL HIER JOUW WAARDEN IN)
        V_MIN = 0.33   # Voltage bij 0 bar (0.5V bij 5V)
        V_MAX = 2.97   # Voltage bij maximale druk (4.5V bij 5V)
        P_MIN = 0.0   # Minimale druk in bar
        P_MAX = 10.34  # Maximale druk in bar (sensor gaat van 0-150 psi)

        # Als het voltage lager is dan het minimum, is de druk 0 (voorkomt negatieve getallen door ruis)
        if voltage <= V_MIN:
            return 1.0

        # 3. Bereken de uiteindelijke druk via lineaire interpolatie
        overdruk = (voltage - V_MIN) * (P_MAX - P_MIN) / (V_MAX - V_MIN) + P_MIN
        
        # Rond af op 2 decimalen voor een nette weergave
        return 1 + round(overdruk, 2)

class LED_Rings_3:
    ### CLASS voor 3 LED-rings met elk 24 LEDs
    # ctor
    def __init__(self, pixels: neopixel):
        self.__pixels = pixels
    
    # properties
    # ********** property pixels - (getter only) ***********
    @property
    def pixels(self) -> neopixel:
        """ The pixels property. """
        return self.__pixels
    
    # extra methods
    def bereken_aantal_leds(self, waarde: float, waarde_max: float):
        aantal_leds = int(round((waarde / waarde_max) * 24, 0))
        return aantal_leds
        

    def set_color(self, color1: int, ncolor1: int, color2: int, ncolor2: int, color3: int, ncolor3: int):
        
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
        
        color_none = 0x000000
        
        # Add offset for every ring to start at the right point
        # RING 1: 0-23
        # RING 2: 24-47
        # RING 3: 48-71
        if (color1 != None):
            for i in range(ncolor1):
                self.pixels[0 + i] = color1  # +0 offset
            for i in range(24-ncolor1):
                self.pixels[0 + ncolor1 + i] = color_none
         
        if (color2 != None):
            for i in range(ncolor2):
                self.pixels[24 + i] = color2  # +24 offset
            for i in range(24-ncolor2):
                self.pixels[24 + ncolor2 + i] = color_none
        
        if (color3 != None):
            for i in range(ncolor3):
                self.pixels[48 + i] = color3  # +48 offset
            for i in range(24-ncolor3):
                self.pixels[48 + ncolor3 + i] = color_none
                
        self.pixels.show()


class Lcd_i2c():
    # ctor
    def __init__(self, PCF8574_adres: int, rs_pin: int, e_pin: int) -> None:
        self.__PCF_adres = PCF8574_adres
        self.__register_set = rs_pin
        self.__enable_klok = e_pin
        
        self.__i2c = SMBus()
        self.i2c.open(1)
        self.setup()
    
    # properties
    # ********** property PCF_adres - (getter only) ***********
    @property
    def PCF_adres(self) -> int:
        """ The PCF_adres property. """
        return self.__PCF_adres
    
    # ********** property register_set - (getter only) ***********
    @property
    def register_set(self) -> int:
        """ The register_set property. """
        return self.__register_set
    
    # ********** property enable_klok - (getter only) ***********
    @property
    def enable_klok(self) -> int:
        """ The enable_klok property. """
        return self.__enable_klok
    
    # ********** property i2c - (getter only) ***********
    @property
    def i2c(self) -> SMBus:
        """ The i2c property. """
        return self.__i2c
    
    # extra methodes
    def setup(self):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.register_set, GPIO.OUT)
        GPIO.setup(self.enable_klok, GPIO.OUT)

        GPIO.output(self.register_set, GPIO.LOW)
        GPIO.output(self.enable_klok, GPIO.LOW)
        
        cursor_instelling = 0x08 | 0x01 << 2 | 0x01 << 1 | 0x01  # alles aan (Display, Cursor, Blink)
        
        self.send_instruction(0x38)  # Function set
        self.send_instruction(cursor_instelling)  # Display on
        self.send_instruction(0x01)  # Clear display & Cursor home


    def send_instruction(self, value):
        GPIO.output(self.register_set, GPIO.LOW)
        # print(f"instruction: {value}")
        
        self.i2c.write_byte(self.PCF_adres, value)
        
        GPIO.output(self.enable_klok, GPIO.HIGH)
        time.sleep(0.005)
        GPIO.output(self.enable_klok, GPIO.LOW)
        time.sleep(0.005)

    def send_charachter(self, value):
        GPIO.output(self.register_set, GPIO.HIGH)
        # print(f"charachter: {value}")
        
        self.i2c.write_byte(self.PCF_adres, value)
        
        GPIO.output(self.enable_klok, GPIO.HIGH)
        time.sleep(0.005)
        GPIO.output(self.enable_klok, GPIO.LOW)
        time.sleep(0.005)

    def write_message(self, msg: str):
        teller = 0
        for char in msg:
            self.send_charachter(ord(char))
            teller += 1
            # if teller == 16:
            #     self.send_instruction(0x80 | 0x40)  # Set DDRAM: cursor op volgende lijn plaatsen
    
    def close_i2c(self):
        self.send_instruction(0x01)  # Clear display & Cursor home
        self.i2c.close()