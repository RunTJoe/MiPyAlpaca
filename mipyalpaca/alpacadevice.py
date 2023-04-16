from mipyalpaca.alpacaserver import *

# Base class for all Alpaca devices
class AlpacaDevice:   
    def __init__(self, devnr, devname, uniqueid):
        self.device_nr = devnr   # device id
        self.name = devname      # device name
        self.description = "No description"  # device description
        self.driverinfo = "No driver info"   # device driver info
        self.interfaceVersion = 0            # interface version
        self.driverVersion = 0               # interface version
        self.connectedState = False          # connection status
        self.uniqueid = uniqueid             # uid
        self.server = None                   # attached Alpaca Server  
    
    # compose reply
    def reply(self, request, value=None, err_nr=0, err_msg=""):
        return AlpacaServer.reply(request, value, err_nr, err_msg)
    
    # set connection status
    def PUT_connected(self, request):
        val = request.form.get('Connected')
        if (val != "True") and (val != "False"):
            return "Invalid connection value", 400
        self.connectedState = bool(val)
        return self.reply(request)

    # get connection status
    def GET_connected(self, request):
        return self.reply(request, self.connectedState)

    # return device name
    def GET_name(self, request):
        return self.reply(request, self.name)
    
    # return device description
    def GET_description(self, request):
        return self.reply(request, self.description)

    # return device driver info
    def GET_driverinfo(self, request):
        return self.reply(request, self.driverinfo)

    #return device driver version
    def GET_driverversion(self, request):
        return self.reply(request, self.driverVersion)
    
    #return device interface version
    def GET_interfaceversion(self, request):
        return self.reply(request, self.interfaceVersion)

    #return supported (additional) device actions
    def GET_supportedactions(self, request):
        return self.reply(request, [])

    # return setup page
    def setupRequest(self, request):
        return "Setup page"
    

