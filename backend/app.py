from RPi import GPIO
import threading
import time
import asyncio
import socketio
import uvicorn

from datetime import datetime, date
from subprocess import check_output
from models.models_sens import HX_Gewicht, OneWire, Mcp_Druk, LED_Rings_3, Lcd_i2c
import board
import neopixel_spi as neopixel

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from repositories.DataRepository import DataRepository
from models.models_api import Historiek, Historieken, DTOHistoriek, Vat, Vaten, DTOVat, VatMetTijd, VatenMetTijd, Config, ConfigList, DTOConfigValues


# TODO: Add logging
import logging

logging.basicConfig(
    level=logging.INFO,                    # alles ≥ INFO‑niveau tonen
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",         # Europees datum‑formaat
    force=True,                           # herconfigureer bij auto‑reload
)
logger = logging.getLogger(__name__)


# TODO: Add hardware constants
DT_PIN = 5
SCK_PIN = 6
KOELING = 26

BTN_POWEROFF = 12
BTN_STOP = 23
BTN_TARREER = 24
BTN_START = 25

# TODO: global variables (like led_state)
async_loop = None

system_state = True
lcd_state = 1

lcd = Lcd_i2c(0x38, 17, 27)

mcp = Mcp_Druk(1, 0)

# 21245 / 1036 = 20.5068
# Standaard 1 voor ruwe data
kalibratiefactor = 20.50675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675675
hx = HX_Gewicht(DT_PIN, SCK_PIN, kalibratiefactor)

NUM_PIXELS = 72
PIXEL_ORDER = neopixel.GRB
COLORS = (0xFF0000, 0x00FF00, 0x0000FF)
DELAY = 0.1

spi = board.SPI()

pixels = neopixel.NeoPixel_SPI(
    spi, NUM_PIXELS, pixel_order=PIXEL_ORDER, auto_write=False, brightness=0.3
)

rings = LED_Rings_3(pixels)

# ----------------------------------------------------
# App setup
# ----------------------------------------------------

@asynccontextmanager
# Lifespan Manager (Startup/Shutdown)
async def lifespan_manager(app: FastAPI):
    global async_loop
    # Start background taken (process_queue + all_out) op in de applicatie
    async_loop = asyncio.get_running_loop()

    # TODO: Add GPIO setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(KOELING, GPIO.OUT)
    # GPIO.setup(LED_PIN, GPIO.OUT)
    # GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BTN_POWEROFF, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BTN_STOP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BTN_TARREER, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BTN_START, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    logger.info("GPIO initialised")
    
    threading.Thread(
        target=gpio_keep_alive,
        daemon=True               # 🔑 daemon‑threads stoppen automatisch bij app‑exit
    ).start()

    async_loop.create_task(tweede_thread()) # loop.create_task for asyncio world / async tasks
    # Geef controle aan FastAPI/Socket.IO
    yield

    # TODO: GPIO cleanup and goodbye
    mcp.close_spi()
    rings.set_off()
    GPIO.cleanup()
    logger.info("GPIO cleaned up – bye!")


# Create a FastAPI app, add CORS middleware, initialize Socket.IO server + ASGI app, create async queue for messages
app = FastAPI(lifespan=lifespan_manager)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
sio = socketio.AsyncServer(cors_allowed_origins='*', async_mode='asgi', logger=True)
sio_app = socketio.ASGIApp(sio, app)

ENDPOINT = "/api/v1"  # Define the endpoint for the API

# ----------------------------------------------------
# Background Tasks
# ----------------------------------------------------

# TODO: Add GPIO keep alive thread
def gpio_keep_alive():
    """Registreert de knop-callback en houdt de thread 'alive'."""
    global async_loop, hx, mcp, rings, system_state, lcd, lcd_state
    
    def callback_poweroff(channel):
        global async_loop, BTN_POWEROFF, lcd, mcp, rings
        time.sleep(0.5)
        if GPIO.input(BTN_POWEROFF) == 0:
            print("<<<<<< POWEROFF >>>>>>")
            
            future = asyncio.run_coroutine_threadsafe(
                sio.emit("B2F_system_shutdown", {"msg": "Systeem wordt uitgeschakeld"}),
                async_loop
            )
            
            time.sleep(0.5)
            
            mcp.close_spi()
            lcd.close_i2c()
            rings.set_off()
            GPIO.cleanup()
            
            logger.info("Btn: GPIO cleaned up – bye!")
            check_output(["sudo", "poweroff"])
        
        
    def callback_stop_metingen(channel):
        global async_loop, system_state, BTN_STOP
        time.sleep(0.5)
        if GPIO.input(BTN_STOP) == 0:
            print("<<<<<< STOP METINGEN >>>>>>")
            system_state = False
            future = asyncio.run_coroutine_threadsafe(
                sio.emit("B2F_stop_metingen", {"msg": "Metingen voor dit vat zijn gestopt"}),
                async_loop
            )
        
    
    def callback_tarreer(channel):
        global async_loop, hx, BTN_TARREER
        time.sleep(0.5)
        if GPIO.input(BTN_TARREER) == 0:
            print("<<<<<< TARREER WEEGSCHAAL >>>>>>")
            hx.hx_tarreer()
        
    
    def callback_start_metingen(channel):
        global async_loop, system_state, BTN_START
        time.sleep(0.5)
        if GPIO.input(BTN_START) == 0:
            print("<<<<<< START METINGEN >>>>>>")
            # Standaard naam als vat wordt aangemaakt met een knop
            today = date.today()
            today_string = today.strftime("%d/%m/%Y")
            vat_prefix = f"Vat {today_string}"
            print(vat_prefix)
            DataRepository.create_new_keg(vat_prefix)
            system_state = True
        

    # GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, bouncetime=100)
    # GPIO.add_event_callback(BUTTON_PIN, callback_button_pressed)
    GPIO.add_event_detect(BTN_POWEROFF, GPIO.FALLING, bouncetime=100)
    GPIO.add_event_callback(BTN_POWEROFF, callback_poweroff)
    
    GPIO.add_event_detect(BTN_STOP, GPIO.FALLING, bouncetime=100)
    GPIO.add_event_callback(BTN_STOP, callback_stop_metingen)
    
    GPIO.add_event_detect(BTN_TARREER, GPIO.FALLING, bouncetime=100)
    GPIO.add_event_callback(BTN_TARREER, callback_tarreer)
    
    GPIO.add_event_detect(BTN_START, GPIO.FALLING, bouncetime=100)
    GPIO.add_event_callback(BTN_START, callback_start_metingen)
    logger.info("gpio_keep_alive gestart; wacht op (button) events…")

    onewire = OneWire()
    
    druksensor = 0
    
    # LED rings
    NUM_PIXELS = 72
    PIXEL_ORDER = neopixel.GRB
    COLORS = (0xFF0000, 0x00FF00, 0x0000FF)
    DELAY = 0.1

    spi = board.SPI()

    pixels = neopixel.NeoPixel_SPI(
        spi, NUM_PIXELS, pixel_order=PIXEL_ORDER, auto_write=False, brightness=0.3
    )
    
    # Zoek het pad één keer op bij het starten
    path_to_w1_slave = onewire.find_sensor_path()
    
    def get_rpi_ip() -> list[str]:
        # bytes ophalen, omzetten naar tekst (decode)
        # \n weghalen (strip)
        ips = check_output(["hostname", "--all-ip-addresses"]).decode("utf8").strip()
        print(ips)
    
        # Opsplitsen in een list
        ips = ips.split(" ")
        return ips
    
    if path_to_w1_slave is None:
        print("Geen sensor gevonden! Controleer je bedrading en of 1-Wire is ingeschakeld.")
    else:
        print(f"Sensor gevonden op: {path_to_w1_slave}")
    
    while True:
        if system_state == True:
            try:
                laatste_vat = DataRepository.read_keg_latest()
                vat_id = laatste_vat["VatID"]
                
                # GEWICHT
                # get_weight() berekent direct (Meting - Tare) / Kalibratiefactor
                # De '5' betekent dat hij 5 metingen gemiddeld voor een stabiel getal
                gewicht = round(hx.hx_get_weight(5), 3)
                
                # Kleine truc uit de library om de chip stabiel en wakker te houden
                hx.hx_power_down_up()
                if gewicht < 0:
                    gewicht = 0
                print(f"Gewicht: {gewicht} g")
                
                # TEMPERATUUR
                temperatuur = onewire.get_temp(path_to_w1_slave)
                
                print(f"De temperatuur is: {temperatuur} °C")
                
                # DRUK
                waarde = mcp.read_channel(druksensor)
                print(f"waarde MCP: {waarde}")
                druk = mcp.get_druk(waarde)
                print(f"Druk = {druk} bar")
                
                # Wegschrijven naar de database
                if (gewicht is not None) and (isinstance(temperatuur, (float, int))) and (temperatuur is not None) and (druk is not None):
                    DataRepository.create_new_historiek(gewicht, 1, vat_id)
                    DataRepository.create_new_historiek(temperatuur, 2, vat_id)
                    DataRepository.create_new_historiek(druk, 3, vat_id)
            
                    time.sleep(0.01)
                    
                    future = asyncio.run_coroutine_threadsafe(
                        sio.emit("B2F_nieuwe_waarden", {"message": "Nieuwe data in de database"}),
                        async_loop
                    )
                
                # LED-ringen aansturen van de sensorwaarden
                gewicht_max = 2100
                temp_max = 40
                druk_max = 2.5
                leds_sens1 = rings.bereken_aantal_leds(gewicht, gewicht_max)
                leds_sens2 = rings.bereken_aantal_leds(temperatuur, temp_max)
                leds_sens3 = rings.bereken_aantal_leds((druk - 1), (druk_max - 1))
                
                # print(f"Sensor 1 LEDs: {leds_sens1}")
                # print(f"Sensor 2 LEDs: {leds_sens2}")
                # print(f"Sensor 3 LEDs: {leds_sens3}")
            
                color_sens1 = 0x00FF00
                color_sens2 = 0x00FF00
                color_sens3 = 0x00FF00
                
                config_data = DataRepository.read_all_configurations()
                
                for item in config_data:
                    if item["ConfigID"] == 4:
                        tarra_vat = item["Value"]
                    
                    if item["ConfigID"] == 1:
                        alarm_gewicht = item["Value"]
                    
                    if item["ConfigID"] == 2:
                        alarm_temperatuur = item["Value"]
                    
                    if item["ConfigID"] == 3:
                        alarm_druk = item["Value"]
                        
                liter_bier = (gewicht - tarra_vat) / 1000.0 / 1.05
                if liter_bier < 0:
                    liter_bier = 0
                print(f"liter bier: {round(liter_bier, 3)}")
                
                liter_bier_max = 2.1
                temp_max = 40
                druk_max = 2.5
                
                leds_sens1 = rings.bereken_aantal_leds(liter_bier, liter_bier_max)
                leds_sens2 = rings.bereken_aantal_leds(temperatuur, temp_max)
                leds_sens3 = rings.bereken_aantal_leds((druk - 1), (druk_max - 1))
                
                # print(f"Sensor 1 LEDs: {leds_sens1}")
                # print(f"Sensor 2 LEDs: {leds_sens2}")
                # print(f"Sensor 3 LEDs: {leds_sens3}")
                
                color_sens1 = 0x00FF00
                color_sens2 = 0x00FF00
                color_sens3 = 0x00FF00
                
                if liter_bier < alarm_gewicht:
                    color_sens1 = 0xFF0000
                    future = asyncio.run_coroutine_threadsafe(
                        sio.emit("B2F_ALARM_gewicht", {"device_id": 1, "msg": "Het vat is bijna leeg"}),
                        async_loop
                    )
                else:
                    future = asyncio.run_coroutine_threadsafe(
                        sio.emit("B2F_ALARM_gewicht_stop", {"device_id": 1, "msg": "Het vat is nog vol genoeg"}),
                        async_loop
                    )
                
                if temperatuur > alarm_temperatuur:
                    color_sens2 = 0xFF0000
                    future = asyncio.run_coroutine_threadsafe(
                        sio.emit("B2F_ALARM_temp", {"device_id": 2, "msg": "Temperatuur is te hoog"}),
                        async_loop
                    )
                    GPIO.output(KOELING, GPIO.HIGH)
                    DataRepository.create_new_historiek(1, 4, vat_id)
                else:
                    future = asyncio.run_coroutine_threadsafe(
                        sio.emit("B2F_ALARM_temp_stop", {"device_id": 2, "msg": "Temperatuur is koud genoeg"}),
                        async_loop
                    )
                    GPIO.output(KOELING, GPIO.LOW)
                    DataRepository.create_new_historiek(0, 4, vat_id)
                    
                if druk < alarm_druk:
                    color_sens3 = 0xFF0000
                    future = asyncio.run_coroutine_threadsafe(
                        sio.emit("B2F_ALARM_druk", {"device_id": 3, "msg": "Druk is te laag"}),
                        async_loop
                    )
                else:
                    future = asyncio.run_coroutine_threadsafe(
                        sio.emit("B2F_ALARM_druk_stop", {"device_id": 3, "msg": "De druk is in orde"}),
                        async_loop
                    )
                
                future = asyncio.run_coroutine_threadsafe(
                        sio.emit("B2F_tarra_vat", {"device_id": 1, "value": tarra_vat, "msg": "Tarragewicht van het vat"}),
                        async_loop
                    )
                
                rings.set_color(color_sens1, leds_sens1, color_sens2, leds_sens2, color_sens3, leds_sens3)
                
                lcd.send_instruction(0x01)  # Clear display & Cursor home
                
                if lcd_state == 1:
                    ips = get_rpi_ip()
                    wlan0_ip = ips[0]
                    # print(f"\neth0: {eth0_ip}")
                    print(f"wlan0: {wlan0_ip}")
                    
                    lcd.send_instruction(0x80 | 0x00)
                    lcd.write_message(f"Surf naar:")
                    lcd.send_instruction(0x80 | 0x40)
                    lcd.write_message(f"{wlan0_ip:<16}")
                    
                if lcd_state == 2:
                    lcd.send_instruction(0x80 | 0x00)
                    lcd.write_message(f"Inhoud vat:")
                    lcd.send_instruction(0x80 | 0x40)
                    lcd.write_message(f"{round(liter_bier, 3)} liter")
                    
                if lcd_state == 3:
                    lcd.send_instruction(0x80 | 0x00)
                    lcd.write_message(f"Temperatuur:")
                    lcd.send_instruction(0x80 | 0x40)
                    lcd.write_message(f"{round(temperatuur, 3)} °C")
                    
                if lcd_state == 4:
                    lcd.send_instruction(0x80 | 0x00)
                    lcd.write_message(f"Druk:")
                    lcd.send_instruction(0x80 | 0x40)
                    lcd.write_message(f"{round(druk, 3)} bar") 
                
                lcd_state += 1
                if lcd_state > 4:
                    lcd_state = 1
                
                time.sleep(2)
            except Exception as ex:
                print(f"GPIO mislukt: {ex}")
                time.sleep(2)


# TODO: Hernoem allesuit thread
async def allesuit():
    pass
#     print("[allesuit] Gestart. Alles uit!")
#     DataRepository.update_status_alle_lampen(0)
    
#     # SOME GPIO OPERATION(S) to turn the LED off
#     GPIO.output(LED_PIN, False)

#     # 1) B2F_alles_uit
#     await sio.emit('B2F_alles_uit', {'status': 'connected'})

#     # 2) B2F_status_lampen => updated states
#     new_statuses = DataRepository.read_status_lampen()
#     await sio.emit('B2F_status_lampen', {'lampen': new_statuses})

#     return {"message": "Alles uit!"}


async def tweede_thread():
    # This function is called every 10 seconds to set all lights to OFF
    # and emit the status to all connected clients.
    print("[alles_uit] Gestart.")
    while True:
        await allesuit()
        await asyncio.sleep(10)


# ----------------------------------------------------
# FastAPI Endpoints
# ----------------------------------------------------


@app.get("/")
async def root():
    return "Server werkt, maar hier geen API endpoint gevonden."

@app.post(ENDPOINT + "/history", response_model=Historiek, status_code=status.HTTP_201_CREATED, summary="Add History", response_description="Add one Historic", 
          responses={404: {'description':'Historics not found'}, 400: {'description':'Historics not added'}}, tags=["History"])
async def new_historiek(historiek: DTOHistoriek):
    response_id = DataRepository.create_new_historiek(historiek.value, historiek.device_id, historiek.vat_id)  # NO ID
    
    if response_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Historics not added")
    
    data = DataRepository.read_history_by_id(response_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Historics not found")
    
    return Historiek(historiek_id=data["HistoriekID"], tijdstip=data["Tijdstip"], 
                     value=data["Value"], device_id=data["DeviceID"], vat_id=data["VatID"])


@app.get(ENDPOINT + "/history/device/{id}/latest", response_model=Historiek, summary="latest data by sensor", responses={404: {'description':'Historic not found'}}, 
         response_description="Latest history of 1 device", tags=["History"])
async def latest_historiek_by_device_id(id: int):
    data = DataRepository.read_latest_data_by_device(id)
    
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Historic not found")
    if isinstance(data["Value"], str) or data["Value"] == "" or data["Value"] is None:
        data["Value"] = 0.0
    return Historiek(historiek_id=data["HistoriekID"], tijdstip=data["Tijdstip"], 
                     value=data["Value"], device_id=data["DeviceID"], vat_id=data["VatID"])


@app.get(ENDPOINT + "/history/device/{device_id}/vat/latest", response_model=Historieken, summary="History", responses={404: {'description':'Historics not found'}}, 
         response_description="All history of a device", tags=["History"])
async def history_by_device_and_latest_keg(device_id: int):
    data = DataRepository.read_history_by_device_and_latest_keg(device_id)
    
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Historics not found")
    
    list_historieken = []
    for item in data:
        item = Historiek(historiek_id=item["HistoriekID"], tijdstip=item["Tijdstip"], 
                     value=item["Value"], device_id=item["DeviceID"], vat_id=item["VatID"])
        list_historieken.append(item)
    
    return Historieken(history=list_historieken)
 
    
@app.get(ENDPOINT + "/history/device/{device_id}/vat/{vat_id}", response_model=Historieken, summary="History", 
         responses={404: {'description':'Historics not found'}}, response_description="All history of a device", tags=["History"])
async def history_by_device_and_keg(device_id: int, vat_id:int):
    data = DataRepository.read_history_by_device_and_keg(device_id, vat_id)
    
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Historics not found")
    
    list_historieken = []
    for item in data:
        item = Historiek(historiek_id=item["HistoriekID"], tijdstip=item["Tijdstip"], 
                     value=item["Value"], device_id=item["DeviceID"], vat_id=item["VatID"])
        list_historieken.append(item)
    
    return Historieken(history=list_historieken)


@app.post(ENDPOINT + "/vaten", response_model=Vat, status_code=status.HTTP_201_CREATED, summary="Add keg", response_description="Add one keg", 
          responses={404: {'description':'Keg not found'}, 400: {'description':'Keg not added'}}, tags=["Kegs"])
async def new_keg(vat: DTOVat):
    response_id = DataRepository.create_new_keg(vat.naam)  # NO ID
    print(f"response_id = {response_id}")
    
    if response_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Keg not added")
    
    data = DataRepository.read_keg_by_id(response_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keg not found")
    
    return Vat(vat_id=data["VatID"], naam=data["VatNaam"])


@app.get(ENDPOINT + "/vaten/latest", response_model=Vat, summary="one Keg", responses={404: {'description':'Keg not found'}}, 
         response_description="One Keg", tags=["Kegs"])
async def latest_keg():
    data = DataRepository.read_keg_latest()
    
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keg not found")
    
    return Vat(vat_id=data["VatID"], naam=data["VatNaam"])


@app.post(ENDPOINT + "/weegschaal/tarreer",response_model=None, summary="Scale tare", responses={404: {'description':'Keg not found'}}, 
         response_description="Tare the scale", tags=["Kegs"])
async def tarreer_weegschaal():
    global hx
    hx.hx_tarreer()
    

@app.get(ENDPOINT + "/vaten/dates/{start_date}/{end_date}", response_model=VatenMetTijd, summary="one Keg by timeperiod", 
         responses={404: {'description':'Kegs not found'}, 400: {'description':'No kegs in this period'}}, 
         response_description="One Keg by timeperiod", tags=["Kegs"])
async def all_kegs_between_dates(start_date: date, end_date: date):
    data = DataRepository.read_kegs_between_dates(start_date, end_date)
    
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kegs not found")
    
    list_vaten = []
    for item in data:
        item = VatMetTijd(vat_id=item["VatID"], naam=item["VatNaam"], aanmaakdatum=item["Aanmaakdatum"])
        list_vaten.append(item)
    
    if list_vaten == []:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No kegs in this period")
    
    return VatenMetTijd(vaten=list_vaten)  


@app.get(ENDPOINT + "/config", response_model=ConfigList, summary="Configurations", responses={404: {'description':'Configs not found'}}, 
         response_description="All configuration settings", tags=["Config"])
async def all_configurations():
    data = DataRepository.read_all_configurations()
    
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configs not found")
    
    list_config = []
    for item in data:
        item = Config(config_id=item["ConfigID"], naam=item["ConfigNaam"], value=item["Value"], sensor_id=item["SensorID"])
        list_config.append(item)
    
    return ConfigList(settings=list_config)


@app.put(ENDPOINT + "/config", response_model=ConfigList, summary="Update configs", response_description="Update configuration", tags=[""],
         responses={404: {'description':'Configs not found'}, 204: {'description':'Configs not updated'}})
async def update_model(config: DTOConfigValues):
    # Controleren of het bestaat
    data = DataRepository.read_all_configurations()
    if len(data) != 4:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configs not found")
    
    aantal_updates = DataRepository.update_all_configurations(config.ALARM_gewicht, config.ALARM_temp, config.ALARM_druk, config.tarragewicht)
    
    if aantal_updates == 0:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Weight not updated")
    
    data = DataRepository.read_all_configurations()
    
    list_config = []
    for item in data:
        item = Config(config_id=item["ConfigID"], naam=item["ConfigNaam"], value=item["Value"], sensor_id=item["SensorID"])
        list_config.append(item)
    
    return ConfigList(settings=list_config)


@app.post(ENDPOINT + "/history/stop",response_model=None, summary="Metingen stop", 
         response_description="Stop monitoring", tags=["History"])
async def stop_metingen():
    global system_state
    print("<<<<<< STOP METINGEN >>>>>>")
    system_state = False

@app.post(ENDPOINT + "/history/start",response_model=None, summary="Metingen start", 
         response_description="Start monitoring", tags=["History"])
async def stop_metingen():
    global system_state
    print("<<<<<< START METINGEN >>>>>>")
    system_state = True
    
@app.post(ENDPOINT + "/system/shutdown", response_model=None, summary="System poweroff", 
         response_description="Shutdown system and RPi")
async def system_shutdown():
    print("<<<<<< POWEROFF >>>>>>")
    await sio.emit("B2F_system_shutdown", {"msg": "Systeem wordt uitgeschakeld"})
    
    # time.sleep(0.5)
    
    mcp.close_spi()
    lcd.close_i2c()
    rings.set_off()
    
    GPIO.cleanup()
    logger.info("Web: GPIO cleaned up – bye!")
    check_output(["sudo", "poweroff"])

# ----------------------------------------------------
# Socket.IO Handlers
# ----------------------------------------------------


@sio.event
async def connect(sid, environ):
    print(f"[Socket.IO] Client geconnecteerd: {sid}")
    # lampenstatus = DataRepository.read_status_lampen()
    # await sio.emit('B2F_status_lampen', {'lampen': lampenstatus}, to=sid)

# ----------------------------------------------------
# Run the app
# ----------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting Uvicorn server")
    uvicorn.run(sio_app, host="0.0.0.0", port=8000, log_level="info")
