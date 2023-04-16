# switchExample2: Alpaca switch device with temperature sensor

import onewire
import uasyncio
import wlancred   # contains WLAN SSID and password
from mipyalpaca.alpacaserver import AlpacaServer
from mipyalpaca.mipyalpacaswitch import MiPySwitchDevice
from machine import Pin
from onewire import OneWire
from ds18x20 import DS18X20

curr_temp = 0   # store lates temperature measurement in global variable


class ExampleSwitchDevice(MiPySwitchDevice):
    def __init__(self, devnr, devname, uniqueid, config_file):
        super().__init__(devnr, devname, uniqueid, config_file)

    # get switch value
    def getswitchvalue(self, id):
        global curr_temp
        
        if id == 4:
            return curr_temp   # return current temperature for switch ID 4
        else:
            return super().getswitchvalue(id)
    
    
async def appGetTemp():
    global curr_temp
    while True:
        sensor_ds.convert_temp()                     # start temperature measurement
        await uasyncio.sleep_ms(1000)                # wait (at least 750ms)
        curr_temp = sensor_ds.read_temp(devices[0])  # read and store latest temperature
        await uasyncio.sleep_ms(2000)                # 2s until start of next measurement
    
    
# Asyncio coroutine
async def main():
    uasyncio.create_task(appGetTemp())   
    await AlpacaServer.startServer()


# Init GPIO, OneWire and DS18B20
one_wire_bus = Pin(11)
sensor_ds = DS18X20(OneWire(one_wire_bus))
# scan for sensor
devices = sensor_ds.scan() 
    
# Create Alpaca Server
srv = AlpacaServer("MyPicoServer", "RTJoe", "0.91", "Unknown")

# Install switch device
srv.installDevice("switch", 0, ExampleSwitchDevice(0, "Pico W Switch", "2fba39e5-e84b-4d68-8aa5-fae287abc02d", "switch0_expl2.json"))

# Connect to WLAN
AlpacaServer.connectStationMode(wlancred.ssid, wlancred.password)

# run main function via asyncio
uasyncio.run(main())

