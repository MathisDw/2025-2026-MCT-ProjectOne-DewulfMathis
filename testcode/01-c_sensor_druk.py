from RPi import GPIO
import time
from models.models_sens import Mcp_Druk

mcp = Mcp_Druk(1, 0)
druksensor = 0

teller = 0

try:
    while True:
        print(f"\n{teller}-----------------------------------------------")
        waarde = mcp.read_channel(druksensor)
        print(f"waarde MCP: {waarde}")
        
        druk = mcp.get_druk(waarde)
        print(f"Druk = {druk} bar")
        
        time.sleep(1)
        
        teller+=1

except KeyboardInterrupt:
    print("\nProgramma gestopt door toetsenbord! (ctrl+C)")

finally:
    GPIO.cleanup()
    mcp.close_spi()