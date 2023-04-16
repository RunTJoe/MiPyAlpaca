from mipyalpaca.alpacaserver import *
from mipyalpaca.alpacadevice import AlpacaDevice

# ASCOM Alpaca switch device
class SwitchDevice(AlpacaDevice):
    
    def __init__(self, devnr, devname, uniqueid, config_file):
        super().__init__(devnr, devname, uniqueid)
        self.interfaceVersion = 2   # this implementation supports switch interface version 2
        self.maxswitch = 0  # number of switches
        self.switchdescr = []  # switch configuration0
        self.switchValue = []  # current switch values
        self.driverinfo = "MicroPython ASCOM Alpaca Switch Driver" # switch driver MiPy
        self.driverVersion = "v0.90"   # driver version
        self.configfile = config_file  # name of JSON file with switch config

        self.switchdescr = readJson(self.configfile)  # load switch configuration
        self.maxswitch = len(self.switchdescr)        # get number of switches
        # create initial list of switch values
        for i in range(self.maxswitch):
            self.switchValue.append(0)               


    # get switch id from request
    def getSwitchId(self, request):
        try:
            idarg = getArg(request, "Id")
            
            # N.I.N.A compatibility workaround
            if idarg == None:
                idarg = getArg(request, "ID")
                
            id = int(idarg)
        except (ValueError, TypeError):
           raise CallArgError("Switch ID invalid")
        # range check
        if (id < 0) or (id >= self.maxswitch):
           raise RangeError("Switch ID out of range or missing")
        return id


    # get switch value (might be overwritten for user specific switches)
    def getswitchvalue(self, id):
        return self.switchValue[id]

    # request for switch value
    def GET_getswitchvalue(self, request):
        id = self.getSwitchId(request)
        return self.reply(request, self.getswitchvalue(id))    

    # get boolean switch value (might be overwritten for user specific switches)
    def getswitch(self, id):
        return bool(self.switchValue[id])

    # request for boolean switch value
    def GET_getswitch(self, request):
        id = self.getSwitchId(request)
        return self.reply(request, self.getswitch(id))

    # set switch value (might be overwritten for user specific switches)
    def setswitchvalue(self, id, value):
        self.switchValue[id] = value
    
    # request for setting switch value
    def PUT_setswitchvalue(self, request):
        id = self.getSwitchId(request)
        # raise exception for non-writable switches        
        if self.switchdescr[id]["canwrite"] == False:
            raise NotImplementedError("Device cannot be written to")
        
        if request.form.get('Value') is None:
            raise CallArgError("Invalid or missing switch value")
        
        v = float(request.form.get("Value"))
        # range check
        if (v < self.switchdescr[id]["min"]) or (v > self.switchdescr[id]["max"]):
           raise RangeError("Value of switch "+str(id)+" out of range or missing")

        self.setswitchvalue(id, v)
        return self.reply(request, "")


    # set boolean switch value (might be overwritten for user specific switches)
    def setswitch(self, id, value):
        self.switchValue[id] = round(value)   

    # request for setting boolean switch value
    def PUT_setswitch(self, request):
        id = self.getSwitchId(request)

        # raise exception for non-writable switches        
        if self.switchdescr[id]["canwrite"] == False:
            raise NotImplementedError("Device cannot be written to")

        if request.form.get("State") == "True":
            self.setswitch(id, 1)
        else:
            if request.form.get("State") == "False":
                self.setswitch(id, 0)
            else:
                raise CallArgError("Invalid or missing switch state")
        return self.reply(request, "")

    # return number of switches
    def GET_maxswitch(self, request):
        return self.reply(request, self.maxswitch)

    # return switch name
    def GET_getswitchname(self, request):
        return self.reply(request, self.switchdescr[int(self.getSwitchId(request))]["name"])
    
    # set new switch name
    def PUT_setswitchname(self, request):
        if request.form.get('Name') is None:
            raise CallArgError("Invalid or missing switch name")
        self.switchdescr[self.getSwitchId(request)]["name"] = request.form.get('Name')
        # write value to config file
        writeJson(self.configfile, self.switchdescr)
        return self.reply(request)

    # return "canwrite" flag
    def GET_canwrite(self, request):
        return self.reply(request, self.switchdescr[self.getSwitchId(request)]["canwrite"])

    # return switch description
    def GET_getswitchdescription(self, request):
        return self.reply(request, self.switchdescr[self.getSwitchId(request)]["descr"])

    # return minimum switch value
    def GET_minswitchvalue(self, request):
        return self.reply(request, self.switchdescr[self.getSwitchId(request)]["min"])

    # return maximum switch value
    def GET_maxswitchvalue(self, request):
        return self.reply(request, self.switchdescr[self.getSwitchId(request)]["max"])

    # return switch step size
    def GET_switchstep(self, request):
        return self.reply(request, self.switchdescr[self.getSwitchId(request)]["step"])


