import ujson
import uasyncio
import uselect
import socket
from microdot_asyncio import Microdot
from microdot_utemplate import render_template
from microdot_asyncio import Response
import network


alpaca_app = Microdot()

# Read JSON file from filename
def readJson(filename):
    with open(filename) as fp:
        jdata = ujson.load(fp)    
    fp.close()
    return jdata


# Write JSON to file filename
def writeJson(filename, jdata):
    with open(filename, "w") as fp:
        fp.write(ujson.dumps(jdata))
    fp.close()


# Get Argument "key" from request
def getArg(request, key):
    if request.method == 'PUT':
        # Case sensitive for PUT requests
        return request.form.get(key)
    else:
        # Case insensitive for GET requests
        for rkey,val in request.args.items():
            if rkey.lower() == key.lower():
                return request.args.get(rkey)


# Alpaca error codes
ALPACA_ERR_OK = 0
ALPACA_ERR_NOT_IMPLEMENTED = 1024
ALPACA_ERR_INVALID_VALUE = 1025

AlpacaDeviceTypes = ["camera", "covercalibrator", "dome", "filterwheel", "focuser", "observingconditions", "rotator", "safetymonitor", "switch", "telescope"]

# Command argument exception  (results in HTTP code 400)
class CallArgError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.errnr = ALPACA_ERR_INVALID_VALUE

# Command not implemented exception (results in HTTP code 200)
class NotImplementedError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.errnr = ALPACA_ERR_NOT_IMPLEMENTED

# Argument range error (results in HTTP code 200)
class RangeError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.errnr = ALPACA_ERR_INVALID_VALUE


class AlpacaServer:
    __instance = None
    config = {}
    devices = {}
    wlan = None
    ServerTransactionID = 1
    ServerApiVersions = [1]
    ServerName = ""
    Manufacturer = ""
    ManfVersion = ""
    ManfLocation = ""
    

    def __new__(cls, *args, **kwargs):
        if not AlpacaServer.__instance:
            AlpacaServer.__instance = object.__new__(cls)
        return AlpacaServer.__instance
    
    def __init__(self,srv_name, srv_manufacturer, srv_manvvers, srv_manfloc):
        AlpacaServer.ServerTransactionID = 1
        AlpacaServer.ServerApiVersions = [1]
        AlpacaServer.ServerName = srv_name
        AlpacaServer.Manufacturer = srv_manufacturer
        AlpacaServer.ManfVersion = srv_manvvers
        AlpacaServer.ManfLocation = srv_manfloc
        for dev in AlpacaDeviceTypes:
            AlpacaServer.devices[dev] = []

        AlpacaServer.config = readJson("servercfg.json") 
        uasyncio.create_task(appDiscovery(self))


    # Create reply for request
    @classmethod
    def reply(cls, request, value=None, err_nr=0, err_msg="", mngmnt_api=False):
        AlpacaServer.ServerTransactionID+=1   # increment server transaction ID
        r = {"ServerTransactionID": AlpacaServer.ServerTransactionID, "ErrorNumber": err_nr, "ErrorMessage" : err_msg}
        if not mngmnt_api:
            # return ClientTransactionID of request
            try:
                clid = getArg(request, "ClientTransactionID")
                r["ClientTransactionID"] = int(clid)
            except (ValueError, TypeError):
                return r
        if err_nr == 0:
            r["Value"] = value
        return r


    # install device on Alpaca server
    def installDevice(self, dev_type, dev_nr, newdevice):
        newdevice.device_nr = dev_nr
        AlpacaServer.devices[dev_type].insert(dev_nr, newdevice)
        newdevice.server = self
        
    # return server API versions    
    @classmethod
    def getServerApiVersions(cls):
        return AlpacaServer.ServerApiVersions
        
    # return configured devices    
    @classmethod
    def getConfDevices(cls):
        devtab = []
        for key,devtype in AlpacaServer.devices.items():
            for dev in devtype:
                devtab.append({"DeviceType":key, "DeviceNumber":dev.device_nr, "DeviceName":dev.description, "UniqueID":dev.uniqueid})
        return devtab

    # return server description  
    @classmethod
    def getServerDescr(cls):
        return {"ServerName":AlpacaServer.ServerName, "Manufacturer":AlpacaServer.Manufacturer, "ManufacturerVersion":AlpacaServer.ManfVersion, "Location":AlpacaServer.ManfLocation}

    # call API method from request
    @classmethod
    def callMethod(cls, dev_type, dev_nr, method, request):
        
        if dev_type not in AlpacaServer.devices:
            return "Device type "+dev_type+" not implemented", 400
        if (dev_nr >= len(AlpacaServer.devices[dev_type])) or (dev_nr < 0):
            return "Device "+dev_type+" "+str(dev_nr)+" not installed", 400
        if not hasattr(AlpacaServer.devices[dev_type][dev_nr], request.method+"_"+method):    
            return "Device "+dev_type+" "+str(dev_nr)+" not installed", 400
            
        try:
            # call the requested method
            return getattr(AlpacaServer.devices[dev_type][dev_nr], request.method+"_"+method)(request)
        except CallArgError as e:
            return str(e), 400
        except RangeError as e:
            return AlpacaServer.devices[dev_type][dev_nr].reply(request, "", e.errnr, str(e))
        except NotImplementedError as e:
            return AlpacaServer.devices[dev_type][dev_nr].reply(request, "", e.errnr, str(e))


    # start Microdot Alpaca server
    @classmethod
    async def startServer(cls):
            await alpaca_app.start_server(port=int(AlpacaServer.config["serverPort"]), debug=True)
            
            
    # connect to WLAN in station mode            
    @classmethod
    def connectStationMode(cls, ssid, password):
        wlan = network.WLAN(network.STA_IF)

        if not wlan.isconnected():
            print('Connecting to ' + ssid, end=' ')
            wlan.active(True)
            wlan.connect(ssid, password)
            while not wlan.isconnected():
                pass
        print('\nConnected to IP address ' + wlan.ifconfig()[0])


    # Start as WLAN access point
    @classmethod
    def startAccessPoint(cls, ssid, password):
        wlan = network.WLAN(network.AP_IF)
        
        wlan.config(essid=ssid, password=password)
        wlan.active(True)

        while wlan.active() == False:
          pass
        print('\nAccessPoint active, IP address ' + wlan.ifconfig()[0])


# Alpaca discovery daemon
async def appDiscovery(server):
    srv = server
    s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('',int(srv.config["discoveryPort"])))

    print("Start Discovery")
    poller = uselect.poll()
    poller.register(s, uselect.POLLIN)        

    while True:
       # poll for discovery broadcasts 
       evts = poller.poll(0)
       for sock, evt in evts:
           if evt and uselect.POLLIN:
               # received discovery broadcast
               print("Broadcast received")
               data, address=s.recvfrom(1024)
               # reply with own port
               send_data = "{\n   \"AlpacaPort\":"+srv.config["serverPort"]+"\n}"
               s.sendto(send_data.encode('utf-8'), address)
       await uasyncio.sleep_ms(10)



Response.default_content_type = 'text/html'

# API call
@alpaca_app.route('/api/v1/<devtype>/<int:devnr>/<method>', methods=['GET', 'PUT'])
async def apicall(request,devtype,devnr,method):
    try: # check ClientID
        clid_arg = getArg(request, "ClientID")
        if clid_arg == None:
            return "Invalid ClientID", 400
        clid = int(clid_arg)
    except (ValueError, TypeError):
        return "Invalid ClientID", 400

    try: # check ClientTransactionID
        trid_arg = getArg(request, "ClientTransactionID")
        if trid_arg == None:
            return "Invalid ClientTransactionID", 400
        trid = int(trid_arg)
    except (ValueError, TypeError):
        return "Invalid ClientTransactionID", 400

    if (clid < 0):
        return "Invalid ClientID", 400
    if (trid < 0):
        return "Invalid ClientTransactionID", 400
    
    return AlpacaServer.callMethod(devtype, devnr, method, request)

# root page, redirect to server setup page
@alpaca_app.route('/')
async def index(request):
    return redirect('/setup')

# device setup page
@alpaca_app.route('/setup/v1/<devtype>/<int:devnr>/setup', methods=['GET', 'PUT'])
async def devsetup(request,devtype,devnr):
    return AlpacaServer.devices[devtype][devnr].setupRequest(request)

# return server API versions
@alpaca_app.get('/management/apiversions')
async def get_mgmt_apiversions(request):
    return AlpacaServer.reply(request, AlpacaServer.getServerApiVersions(), mngmnt_api=True)

# return server description
@alpaca_app.get('/management/v1/description')
async def get_mgmt_description(request):
    return AlpacaServer.reply(request, AlpacaServer.getServerDescr(), mngmnt_api=True)

# return configured devices
@alpaca_app.get('/management/v1/configureddevices')
async def get_mgmt_configureddevices(request):
    return AlpacaServer.reply(request, AlpacaServer.getConfDevices(), mngmnt_api=True)

# server setup page
@alpaca_app.route('/setup', methods=['GET', 'POST'])
async def setup(req):
    if req.method == 'POST':  # apply new settings on POST
        AlpacaServer.config["serverPort"] = req.form.get('srvport')
        AlpacaServer.config["discoveryPort"] = req.form.get('discport')
        writeJson("servercfg.json", AlpacaServer.config)
    # render server setup page    
    return render_template('mipysetup.html', title="RasPi Pico Alpaca Server Setup", tab = AlpacaServer.getConfDevices(), srvcfg = AlpacaServer.config)
