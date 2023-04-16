# MiPyAlpaca MicroPython Alpaca Driver

## Introduction

MiPyAlpaca is an ASCOM Alpaca implementation for MicroPython. Currently it’s supporting only the device type “Switch” but can be extended to other devices (I have planned to add “CoverCalibrator” soon). It also supports the Alpaca discovery protocol. I have tested it on Raspberry Pi Pico W and ESP32-C3.

<pictures>

It can be used to make microcontroller-based projects accessible by astronomy software applications (like e.g. N.I.N.A.) or self-written applications via the standardized and operating system independent ASCOM Alpaca protocol.

Simple controlling of input/output pins, setting of PWM values and reading of ADC values can be done even without coding. As the provided switchExample1 demonstrates, you just have to edit a JSON configuration file. Configure the pin functionality, start the software and connect your application.

```json
[
{"switchnr": 0,"name": "GPIO OUT","pincfg": {"pin": 15,"pinfct": "OUTP","initval": 1},"canwrite": true,"min": 0,"max": 1,"step": 1,"swfct": "MiPyPin","descr": "Output test pin"},
{"switchnr": 1,"name": "GPIO In","pincfg": {"pin": 16,"pinfct": "INP","pull": "PULL_DOWN"},"canwrite": false,"min": 0,"max": 1,"step": 1,"swfct": "MiPyPin","descr": "Input test pin"},
{"switchnr": 2,"name": "PWM test","pincfg": {"pin": 14,"pinfct": "PWM","initval": 19000,"freq": 1000},"canwrite": true,"min": 0,"max": 65535,"step": 1,"swfct": "MiPyPin","descr": "PWM test pin"},
{"switchnr": 3,"name": "ADC test","pincfg": {"pin": 28,"pinfct": "ADC"},"canwrite": false,"min": 0,"max": 65535,"step": 1,"swfct": "MiPyPin","descr": "ADC test pin"}
]
```

For the configuration shown above, N.I.N.A will display the following switch device (will be automatically adapted to your pin configuration):

![](D:\Projects\GitHub\MiPyAlpaca\resources\images\SwExample1NINA.jpg)

Now you can set the output pins, read input pins, set PWM outputs and read ADC inputs from N.I.N.A..

Here is a simple breadboard setup testing the example above on a Raspberry Pico W. You can switch on/off one LED with GPIO output pin, read the state of the button, set the brightness of another LED via PWM and read the voltage at the trim potentiometer.

![](D:\Projects\GitHub\MiPyAlpaca\resources\images\SwExample1BBoard.jpg)



If you want to control more sophisticated “Switches”, you can derive a subclass of MiPySwitchDevice and just implement the required functionality in the get and set methods to read and write the switch values. See switchExample2 for details.



## Installation

Copy the files from the GitHub repository on your device. Folders *mipyalpaca* and *templates* shall be subfolders of the folder containing the main application (like e.g. the example files).

MiPyAlpaca requires two additional packages:

- Microdot
  (https://github.com/miguelgrinberg/microdot)

- utemplate
  [https://github.com/pfalcon/utemplate](https://github.com/pfalcon/utemplate)

For installation of these packages see the corresponding documentation. If you use the Thonny IDE (https://thonny.org/), you can also use the Tools/Manage packages function. In Thonny, the file system of my installation looks like that:


![](D:\Projects\GitHub\MiPyAlpaca\resources\images\MiPyAlpacaFiles.jpg)



## Usage

- The recommended starting point is to use one of the provided examples.

- Edit WLAN credentials in wlancred.py

- Assign a new Globally Unique ID (UID) for your device in the call argument of `installDevice `(not absolutely necessary, but recommended)

- If you want to use another discovery port than 32227 (default), or another port for the Alpaca server, edit the port numbers in servercfg.json. 

- Edit switch0.json for your switch configuration (see below for details)

- Start the example program



### Switch configuration

| Attribute | Description                                                                                     |
| --------- | ----------------------------------------------------------------------------------------------- |
| switchnr  | Switch ID                                                                                       |
| name      | Switch name                                                                                     |
| canwrite  | *true* for writable switch<br/>*false* for read-only switch                                     |
| min       | Minumum value                                                                                   |
| max       | Maximum value                                                                                   |
| step      | Value step size                                                                                 |
| swfct     | *MiPyPin* for MicroPython pin (see table below)<br/>*UserDef*  for user defined switch function |
| descr     | switch description                                                                              |

If "swfct" has value "MiPyPin", attribute "pincfg" has to be defined with the following sub-attributes:

| Attribute | Description                                                                        | Remarks                            |
| --------- | ---------------------------------------------------------------------------------- | ---------------------------------- |
| pinfct    | OUTP: Output pin<br/>INP: Input pin<br/>ADC: ADC input pin<br/>PWM: PWM output pin |                                    |
| initval   | Initialisation value                                                               | for OUTP and PWM only<br/>optional |
| pull      | PULL_UP: Pull up<br/>PULL_DOWN: Pull down                                          | for INP only<br/>                  |

If "swfct" has value "Userdef", create a new subclass derived from class SwitchDevice and overwrite the following methods with the required code:

- `getswitchvalue`

- `getswitch`

- `setswitchvalue`

- `setswitch`



## Alpaca Management API

### Main Setup Page

The Alpaca server main setup page can be called by

**http://*host*:*port*/setup** 

where *host* is usually the ip address of your device.

![](D:\Projects\GitHub\MiPyAlpaca\resources\images\MgmtAPIPorts.jpg)



### Device Specific Setup Page(s)

The device specific setup pages can be called by

**http://*host*:*port*/setup/v*apiversion_number*/*device_type*/*device_number*/setup**

As this implementation currently supports only API version v1 and device type "switch", the correct URL for switch device 0 is

**http://*host*:*port*/setup/api/v1/switch/0/setup**



## Examples

The following example applications are provided:

### switchExample1

This is an example with 4 switches, each for one type of the available MicroPython pins:

- 1 Input pin

- 1 Output pin

- 1 ADC pin

- 1 PWM pin
  
  

The example was already described in the introduction above.

### switchExample2

Example with the 4 switches from switchExample1 and 1 additional userdefined switch

The user defined switch is a read-only "switch" providing the temperature values of a DS18B20 temperature sensor.

This example code demonstrates (this is the additional code) how to implement support of a DS18B20 temperature sensor which can be read by the astronomy software:

```python
class ExampleSwitchDevice(MiPySwitchDevice):
    def __init__(self, devnr, devname, uniqueid, config_file):
        super().__init__(devnr, devname, uniqueid, config_file) # get switch value

    def getswitchvalue(self, id):
        global curr_temp

        if id == 4:
            return curr_temp   # return current temperature for switch ID 4
        else:
            return super().getswitchvalue(id)

```

The temparature sensor is read cyclically in an Asyncio coroutine `appGetTemp`, started in parallel to the Alpaca server:

```python
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
```



Here is the switch window of N.I.N.A. for switchExample2 with the temperature gauge:

![](D:\Projects\GitHub\MiPyAlpaca\resources\images\SwExample2NINA.jpg)



This is a sample breadboard setup for this example:

![](D:\Projects\GitHub\MiPyAlpaca\resources\images\SwExample2BBoard.jpg)



## ASCOM Alpaca compliance

MiPyAlpaca was successfully validated by the Conform Universal [ConformU](https://github.com/ASCOMInitiative/ConformU) conformance validation tool to be Alpaca compliant.



# Acknowledgements

Many thanks to Miguel Grinberg for providing his [Microdot](https://github.com/miguelgrinberg/microdot) framework. He has also provided excellent and fast support to my questions and remarks.

Also many thanks to Peter Simpson from the [ASCOM Driver and Application Development Support Forum](https://ascomtalk.groups.io/g/Developer) for answering all my questions regarding the Alpaca protocol.
