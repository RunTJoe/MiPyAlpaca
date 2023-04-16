# switchExample1: Simple Alpaca switch device

import uasyncio
import wlancred   # contains WLAN SSID and password
from mipyalpaca.alpacaserver import AlpacaServer
from mipyalpaca.mipyalpacaswitch import MiPySwitchDevice

# Asyncio coroutine
async def main():
    await AlpacaServer.startServer()


# Create Alpaca Server
srv = AlpacaServer("MyPicoServer", "RTJoe", "0.91", "Unknown")

# Install switch device
srv.installDevice("switch", 0, MiPySwitchDevice(0, "Pico W Switch", "2fba39e5-e84b-4d68-8aa5-fae287abc02d", "switch0_expl1.json"))

# Connect to WLAN
AlpacaServer.connectStationMode(wlancred.ssid, wlancred.password)

# run main function via asyncio
uasyncio.run(main())

