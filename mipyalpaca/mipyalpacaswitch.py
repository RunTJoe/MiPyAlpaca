from mipyalpaca.alpacaswitch import SwitchDevice
from machine import Pin
from machine import PWM
from machine import ADC
from microdot_utemplate import render_template


# MicroPython switch device
# support easy configuration of most common switch functions for MicroPython controllers:
# - GPIO outputs
# - GPIO inputs
# - PWM
# - ADC
class MiPySwitchDevice(SwitchDevice):
    
    def __init__(self, devnr, devname, uniqueid, config_file):
        super().__init__(devnr, devname, uniqueid, config_file)       
        self.description = "MicroPython Alpaca switch device"
        self.swpin = []

        # configure all MicroPython pins
        for i in range(self.maxswitch):
            sw = self.switchdescr[i]
            
            if sw["swfct"] == "MiPyPin":
                cfg = sw["pincfg"]
                pnr = int(cfg["pin"])
                
                if cfg["pinfct"] == "OUTP":
                    # output pin
                    p = Pin(pnr, Pin.OUT)
                    if cfg["initval"] != None:
                        # set initial value
                        self.switchValue[i] = int(cfg["initval"])
                        p.init(value=int(cfg["initval"]))
                        p.value(int(cfg["initval"]))
                    self.swpin.insert(i, p)
                    
                if cfg["pinfct"] == "INP":
                    # input pin
                    p = Pin(pnr, Pin.IN)
                    # setup pullup 
                    if cfg["pull"] == "PULL_UP":
                        p.init(pull=Pin.PULL_UP)
                    if cfg["pull"] == "PULL_DOWN":
                        p.init(pull=Pin.PULL_DOWN)
                    self.swpin.insert(i, p)
                    
                if cfg["pinfct"] == "PWM":
                    # PWM pin
                    p = PWM(Pin(pnr))
                    p.freq(int(cfg["freq"]))
                    if cfg["initval"] != None:
                        # set initial value
                        self.switchValue[i] = int(cfg["initval"])
                        p.duty_u16(int(cfg["initval"]))                   
                    self.swpin.insert(i, p)
                    
                if cfg["pinfct"] == "ADC":
                    # ADC pin
                    p = ADC(Pin(pnr))
                    self.swpin.insert(i, p)
            else:
                self.swpin.insert(i, "UserDef")
                

    # set switch value
    def setswitchvalue(self, id, value):
        super().setswitchvalue(id, value)
        
        sw = self.switchdescr[id]
        if sw["swfct"] == "MiPyPin":
            cfg = sw["pincfg"]
            if cfg["pinfct"] == "OUTP":
                self.swpin[id].value(value)
            if cfg["pinfct"] == "PWM":
                self.swpin[id].duty_u16(int(round(value)))
        

    # set (boolean) switch value
    def setswitch(self, id, value):
        self.setswitchvalue(id, value)


    # get switch value
    def getswitchvalue(self, id):
        super().getswitchvalue(id)
        sw = self.switchdescr[id]
        if sw["swfct"] == "MiPyPin":
            cfg = sw["pincfg"]
            if cfg["pinfct"] == "ADC":
                self.switchValue[id] = self.swpin[id].read_u16()
            if cfg["pinfct"] == "INP":
                self.switchValue[id] = self.swpin[id].value()
        return self.switchValue[id]


    # get (boolean) switch value
    def getswitch(self, id):
        super().getswitch(id)
        sw = self.switchdescr[id]
        if sw["swfct"] == "MiPyPin":
            cfg = sw["pincfg"]
            if cfg["pinfct"] == "INP":
                self.switchValue[id] = self.swpin[id].value()
        return bool(self.switchValue[id])


    # return setup page
    def setupRequest(self, request):
        return render_template('setupswitch0.html', devname=self.name, cfgfile=self.configfile)
