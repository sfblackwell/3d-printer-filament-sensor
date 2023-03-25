import network, rp2
import time
from machine import ADC, Pin

class WiFi:
    def __init__(self, ssid, password, country, fullBattery = 4.0, emptyBattery = 2.5 ):
        self.ssid 		= ssid
        self.password 	= password
        self.country 	= country
        
        self.fullBattery 	= fullBattery    # reference voltages for a full/empty battery
        self.emptyBattery	= emptyBattery  # vary by battery size/manufacturer
        
        self.connectStatus 	= False
        self.ipAddress 		= ""
        
        rp2.country(self.country)
        self.wlan = network.WLAN(network.STA_IF)
        
        # as a part of WiFi setup get voltage suppy mode and battery %
      
        conversion_factor = 3 * 3.3 / 65535
              
        Pin(25, mode=Pin.OUT, pull=Pin.PULL_DOWN).high()	# Make sure pin 25 is high
        Pin(29, Pin.IN) 									# Reconfigure pin 29 as an input.
        vsys = ADC(29)										# voltage adc
        
        self.vSystemVolts = vsys.read_u16() * conversion_factor
        
        Pin(29, Pin.ALT, pull=Pin.PULL_DOWN, alt=7)     	# Restore the pin state and possibly reactivate WLAN  

        isOnUSB = Pin('WL_GPIO2', Pin.IN)
        if isOnUSB.value() == 1:
            self.onUSB = True
        else:
            self.onUSB = False
            
        self.batteryPercentage = 100 * ((self.vSystemVolts - self.emptyBattery) / (self.fullBattery - self.emptyBattery))
        if self.batteryPercentage > 100:
           self.batteryPercentage = 100.00

    def connectWiFi(self):
        
       self.wlan = network.WLAN(network.STA_IF)
       self.wlan.config(pm = 0xa11140)
       self.wlan.active(True)
       self.wlan.connect(self.ssid, self.password)
       
       # try 10 times
       
       max_wait = 10
       while max_wait > 0:
          if self.wlan.status() < 0 or self.wlan.status() >= 3:
            break
          max_wait -= 1
          
          time.sleep(1)

       # handle connection error
       
       if self.wlan.status() != 3:
          self.connectStatus = False
       else:
          self.connectStatus = True
          
          self.status = self.wlan.ifconfig()
          self.ipAddress = self.status[0]
          
       return self.connectStatus

    #	disconnect from network to reduce power

    def disconnectWiFi(self):
        
        self.wlan.disconnect()

    def ipAddressWiFi(self):
        
        return self.ipAddress

    def statusWiFi(self):
        
        return self.connectStatus        

    def isOnUSB(self):
        
        return self.onUSB
    
    def isOnBattery(self):
        
        return not self.onUSB        

    def vSystemV(self):
        
        return self.vSystemVolts
    
    def vSystemP(self):
        
        return self.batteryPercentage    
