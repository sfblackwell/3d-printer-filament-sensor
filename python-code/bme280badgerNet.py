#	show messages etc

DEBUG = True
#DEBUG = False

#	show long messages such as http responses

#DEBUG1 = True
DEBUG1 = False

import badger2040
import badger_os

display = badger2040.Badger2040()

import network
import machine
import ntptime
import time
from breakout_bme280 import BreakoutBME280
import umail
import json
import sys
import urequests
from netmanClass import WiFi
import os, socket
from pimoroni_i2c import PimoroniI2C
import pcf85063a

#	set up badger
#
#	flash LED to show badger is alive & code running

for light in range(0,5):
    display.led(255)
    time.sleep(.25)
    display.led(0)
    time.sleep(.25)

#	RTC delay calculator
#
#	caclulate delay in s/m/h from date
#
def nextAlarm(date, seconds):
    
    year, month, day, hour, minute, second, dow = date
    
    second += seconds
    minute += second // 60
    second %= 60
    hour += minute // 60
    minute %= 60
    day += hour // 24
    hour %= 24
    
    return second, minute, hour

#	Display Setup
#
FONT_NAMES = (
    ("sans", 0.2, 2),
    ("gothic", 0.3, 2),
    ("cursive", 0.2, 2),
    ("serif", 0.2, 2),
    ("serif_italic", 0.2, 2),
    ("bitmap6", 1, 1),
    ("bitmap8", 1, 1),
    ("bitmap14_outline", .8, 1)
)

FONT_NUMBER = 7

fontName, fontSize, fontThickness = FONT_NAMES[FONT_NUMBER]

TEXT_SIZE1   = 3 * fontSize
TEXT_SIZE2   = 4 * fontSize
TEXT_SIZE3   = 2 * fontSize

HEADER_X = 0
HEADER_Y = 0

HUMI_X  	= 0
HUMI_Y 		= 30
HUMI_Y_DATA = 40

HUMI_HEAD_OFF = 33
HUMI_DATA_OFF = 30

TEMP_X 		= 130
TEMP_Y 		= 30
TEMP_Y_DATA = 40

TEMP_HEAD_OFF = 33
TEMP_DATA_OFF = 40

ADDR_X = 0
ADDR_Y = 110

UPDATE_FAST = 2

display.set_update_speed(UPDATE_FAST)
display.set_font(fontName)
display.set_thickness(fontThickness)

WIDTH  = 296
HEIGHT = 128

#	Scan the i2c bus for devices

sdaPIN=machine.Pin(4)
sclPIN=machine.Pin(5)
i2c=machine.I2C(0,sda=sdaPIN, scl=sclPIN, freq=400000)

if DEBUG: 
    print("===> I2C bus scan results:")    
    print(i2c.scan())
    print([hex(x) for x in i2c.scan()])

#	initialise enviormental sensor

if DEBUG: print("===> Initialise BME280 sensor")

BME280 = BreakoutBME280(i2c)

#	load parameters

if DEBUG: print("===> Get parameters")

with open("parameters.json") as parameters:
    loadedParameters = json.load(parameters)

minHumidity  = loadedParameters["minHumidity"]     
maxHumidity  = loadedParameters["maxHumidity"]
sendEmail    = loadedParameters["sendEmail"]
sendSQL      = loadedParameters["sendSQL"]
sqlDataAddr  = loadedParameters["sqlDataAddr"]
waitTime     = loadedParameters["waitTime"]
fullBattery  = loadedParameters["fullBattery"]
emptyBattery = loadedParameters["emptyBattery"]
changeBattery= loadedParameters["changeBattery"]

if DEBUG:
    print("===> Parameter settings")
    print("===> minHumidity", minHumidity)
    print("===> maxHumidity", maxHumidity)
    print("===> sendEmail"	, sendEmail)
    print("===> sendSQL"	, sendSQL)
    print("===> sqlDataAddr", sqlDataAddr)
    print("===> waitTime"	, waitTime)
    print("===> fullBattery", fullBattery)
    print("===> emptyBattery", emptyBattery)
    print("===> changeBattery", changeBattery)    
    
#
#	read email and wifi credentials from json file
#

if DEBUG: print("===> Get eMail and Wifi credentials")

with open("credentials.json") as credentials:
    netCredentials = json.load(credentials)

eMailUser     = netCredentials["eMailUser"]     
eMailPassword = netCredentials["eMailPassword"]
  
smtpGateway = netCredentials["smtpGateway"]
smtpPort = int(netCredentials["smtpPort"])     
eMailTo   = netCredentials["eMailTo"]
eMailFrom = netCredentials["eMailFrom"]

if DEBUG:
    print("===> eMail settings")
    print("===> smtpGateway", smtpGateway)
    print("===> smtpPort", smtpPort) 
    print("===> eMailTo", eMailTo)
    print("===> eMailFrom", eMailFrom)

sqlSecret = netCredentials["sqlSecret"]

if DEBUG: print("===> eMail and WiFi credentials loaded")

#	setup WiFi

if DEBUG: print("===> Setup WiFi")

country  = netCredentials['country']  
ssid     = netCredentials['ssid']     
password = netCredentials['password']

#	setup WiFi class  

wifiConnection = WiFi(ssid, password, country, fullBattery, emptyBattery)

onUSB 				= wifiConnection.isOnUSB()
onBattery 			= wifiConnection.isOnBattery()
batteryPercentage 	= wifiConnection.vSystemP()
vSystemVolts 		= wifiConnection.vSystemV()

if DEBUG: print("===> onUSB: "      , onUSB)
if DEBUG: print("===> onBattery: "  , onBattery)        
if DEBUG: print("===> vSystemVolts: "    , vSystemVolts)
if DEBUG: print("===> batteryPercentage: ", batteryPercentage)

#	open network connection and handle the RTC's, yes all of them
    
if DEBUG: print("\n===> Initial network connection")

WiFiConnected = False
updateMessage = ""
try:
    WiFiConnected = wifiConnection.connectWiFi()
    if WiFiConnected:
        if DEBUG: print("===> Setup Pico RTC & Badger RTC based on NTP time")
        
        #	badger RTC is connected via i2c, then setup alarm and interupt settings
        
        i2c = PimoroniI2C(sda=4,scl=5)
        badger_rtc = pcf85063a.PCF85063A(i2c)
        
        badger_rtc.clear_alarm_flag()
        badger_rtc.enable_alarm_interrupt(True)
        badger_rtc.enable_timer_interrupt(True)
        
        #	set RTC's from  NTP
        
        pico_rtc = machine.RTC() 
        ntptime.settime()
        badger_rtc.datetime(time.localtime())        
        
        uyear, umonth, uday, uhour, uminute, usecond, udow, udummy    = time.gmtime()
        lyear, lmonth, lday, lhour, lminute, lsecond, ldow, ldummy    = time.localtime()        
        byear, bmonth, bday, bhour, bminute, bsecond, bdow            = badger_rtc.datetime()
        pyear, pmonth, pday, pdow,  phour,   pminute, psecond, pdummy = pico_rtc.datetime()

        timeString = "{:02}:{:02}:{:02} {:04}/{:02}/{:02}"
        
        hmsymdUTC    = timeString.format(uhour, uminute, usecond, uyear, umonth, uday)
        hmsymdLocal  = timeString.format(lhour, lminute, lsecond, lyear, lmonth, lday)
        hmsymdPico   = timeString.format(phour, pminute, psecond, pyear, pmonth, pday)
        hmsymdBadger = timeString.format(bhour, bminute, bsecond, byear, bmonth, bday)
    
        if DEBUG: print("===> UTC time:  "  , hmsymdUTC)
        if DEBUG: print("===> Local time:  ", hmsymdLocal)
        if DEBUG: print("===> Pico Time:  " , hmsymdPico)
        if DEBUG: print("===> Badger Time: ", hmsymdBadger)
        
        timeString1 = "{:02}:{:02}:{:02}"
        alarm = nextAlarm(badger_rtc.datetime(), waitTime)
        if DEBUG: print("===> Alarm set for: ", timeString1.format(alarm[2], alarm[1], alarm[0]))
        badger_rtc.set_alarm(*alarm)       

        ipAddress = wifiConnection.ipAddressWiFi()
        updateMessage = updateMessage + "(" + ipAddress + ")"
        onWiFi =" W"
        if DEBUG: print("===> WiFi Connected, returned IP address", ipAddress)
    else:
        onWiFi =""
        updateMessage = updateMessage + "(WiFi connection error)"
        if DEBUG: print("===> WiFi connection Error")
except:
    onWiFi =""
    updateMessage = updateMessage + "(WiFi connection error)"
    if DEBUG: print("===> WiFi connection error")
    WiFiConnected = False


if DEBUG: print("===> Lets update badger")

runError = False

#
#	this block, reads BM280 and sets up display
#

try:

    #	re read rtc
    
    year, month, day, wd, hour, minute, second, _ = pico_rtc.datetime()
    hms = "{:02}:{:02}".format(hour, minute, second)
    ymd = "{:04}/{:02}/{:02}".format(year, month, day)

    if DEBUG: print("===> hour, minute, second", hms)
    if DEBUG: print("===> year, month, day", ymd)
    
    # Page Header

    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    
    display.text( "{:.2f}V {:.0f}% {}{}".format(vSystemVolts, batteryPercentage, hms, onWiFi), HEADER_X, HEADER_X, WIDTH, TEXT_SIZE1 )
  
    if DEBUG: print("===> Reading BME280")
    
    #	do a dummy read
    
    BME280Reading = BME280.read()
    time.sleep(5)
    BME280Reading = BME280.read()

    BME280temperature=BME280Reading[0]
    BME280pressure   =BME280Reading[1]
    BME280humidity   =BME280Reading[2]
    
    if DEBUG: print("===> BME280 readings: ", BME280temperature, BME280pressure, BME280humidity )
    
    humidityHeader 	  =  "Rh %"
    temperatureHeader =  "Temp"
    humidityText 	  = "{humidity:.2f}"
    temperatureText   = "{temperature:.2f}"       
    pressureText      = "{pressure:.2f}"
    
    #display.text(text, x, y, wordwrap, scale, angle, spacing)
    
    #	display data header
    
    display.text(humidityHeader, HUMI_X + HUMI_HEAD_OFF, HUMI_Y, WIDTH, TEXT_SIZE2 )
    display.text(temperatureHeader, TEMP_X + TEMP_HEAD_OFF, TEMP_Y, WIDTH, TEXT_SIZE2 )

    #	display data

    display.text(humidityText.format(humidity=BME280humidity)   , HUMI_X + HUMI_DATA_OFF, TEMP_Y + TEMP_Y_DATA, WIDTH, TEXT_SIZE2 )
    display.text(temperatureText.format(temperature=BME280temperature), TEMP_X + TEMP_DATA_OFF, TEMP_Y + TEMP_Y_DATA, WIDTH, TEXT_SIZE2 )
     
    if DEBUG: print("===> Initial display created ")
     
except:
    if DEBUG: print("===> Error reading BME280 and updating display")
    display.text("Error reading BME280 and updating display", ADDR_X, ADDR_Y, WIDTH, TEXT_SIZE3)
    display.update()
    runError = True

#
#	if no errors this block sends REST & eMail updates via WiFi connection
#

if runError == False:  
    try:
        if WiFiConnected:
            
            #	this block sends sql data to server
        
            if sendSQL == "yes":
                updateURL = sqlDataAddr
                updateURL = updateURL + "?sqlsecret="   + sqlSecret
                updateURL = updateURL + "&temperature=" + temperatureText.format(temperature=BME280temperature)
                updateURL = updateURL + "&humidity="    + humidityText.format(humidity=BME280humidity)
                updateURL = updateURL + "&pressure="    + pressureText.format(pressure=BME280pressure)
                
                if onBattery == True:
                    updateURL = updateURL + "&onBattery=yes"
                else:
                    updateURL = updateURL + "&onBattery=no"
                    
                updateURL = updateURL + "&batteryPercentage="   + "{:.2f}".format(batteryPercentage)
                updateURL = updateURL + "&vSystemVolts="    	+ "{:.2f}".format(vSystemVolts) 

                updateURL = updateURL + "&fullBattery="   + "{:.2f}".format(fullBattery) 
                updateURL = updateURL + "&emptyBattery="  + "{:.2f}".format(emptyBattery) 
                updateURL = updateURL + "&changeBattery=" + "{:.2f}".format(changeBattery) 

                if DEBUG1: print("===>",updateURL)
                sqlRequest = urequests.get(url = updateURL)
                if DEBUG1: print("===>\n", sqlRequest.text, "\n<===")
                 
                if DEBUG: print("===> SQL Updated")
                updateMessage = updateMessage + "(SQL updated)"
                     
            #	this block builds and sends eMail

            if sendEmail == "yes":
                if DEBUG: print("===> Checking if email response is needed")
                if (BME280Reading[2] < minHumidity or BME280Reading[2] > maxHumidity):

                    smtp = umail.SMTP(smtpGateway, smtpPort)
                    smtp.login(eMailUser, eMailPassword)
                        
                    smtp.to(eMailTo)
                    smtp.write("From: " + eMailFrom + "\n")
                    smtp.write("To: " + eMailTo + "\n")
                    smtp.write("Subject: Humidity = " + humidityText.format(humidity=BME280Reading[2]) + "\n\n")
                    smtp.write("Humidity:	" + humidityText.format(humidity=BME280Reading[2]) + "\n")
                    smtp.write("Temperature:" + temperatureText.format(temperature=BME280Reading[0]) + "\n")

                    smtp.write("\n\n")
                    if onBattery == True:
                        smtp.write("onBattery: Yes\n")
                    else:
                        smtp.write("onBattery: No\n")
                        
                    smtp.write("batteryPercentage: {:.2f} \n".format(batteryPercentage))
                    smtp.write("vSystemVolts: {:.2f} \n".format(vSystemVolts))
                    smtp.write("changeBattery: {:.2f} \n".format(changeBattery))
                    smtp.write("\n\n")

                    smtp.send()
                    smtp.quit()
                    
                    updateMessage = updateMessage + "(eMail Sent)"
                    if DEBUG: print("===> eMail Sent")
                    
            #	send battery change email                       
                    
            if DEBUG: print("===> Checking if change battery email needed")
            if (vSystemVolts < changeBattery):

                smtp = umail.SMTP(smtpGateway, smtpPort)
                smtp.login(eMailUser, eMailPassword)
                    
                smtp.to(eMailTo)
                smtp.write("From: " + eMailFrom + "\n")
                smtp.write("To: " + eMailTo + "\n")
                smtp.write("Subject: Change fillament sensor batteries\n\n")

                smtp.write("\n\n")
                if onBattery == True:
                    smtp.write("onBattery: Yes\n")
                else:
                    smtp.write("onBattery: No\n")
                    
                smtp.write("batteryPercentage: {:.2f} \n".format(batteryPercentage))
                smtp.write("vSystemVolts: {:.2f} \n".format(vSystemVolts))
                smtp.write("\n\n")
                smtp.write("fullBattery: {:.2f} \n".format(fullBattery))
                smtp.write("emptyBattery: {:.2f} \n".format(emptyBattery))
                smtp.write("changeBattery: {:.2f} \n".format(changeBattery))                  
                smtp.write("\n\n")

                smtp.send()
                smtp.quit()
                
                updateMessage = "(Change battery)" + updateMessage
                if DEBUG: print("===> Change battery eMail sent")                        
                    
        else:
            if DEBUG: print("===> WiFi not connected, No SQL/Email update")
                    
    except:
        if DEBUG: print("===>"+ updateURL)
        if DEBUG: print("===> Error with network update")
        updateMessage = updateMessage + "(Error with network update)"

#
#	end of update block
#
# clean up and get ready for next run
#

try:
    if WiFiConnected:
        wifiConnection.disconnectWiFi()
        if DEBUG: print("===> Disconnected from WiFi")
except:
    if DEBUG: print("===> Error disconnecting from WiFi")
    updateMessage = updateMessage + "(Error disconnecting from WiFi)"

# finaly update screen

if DEBUG: print("===> Complete the display update")
display.text(updateMessage, ADDR_X, ADDR_Y, WIDTH, TEXT_SIZE3)
display.update()

if DEBUG: print("===> Waiting for next update")
if DEBUG: print("=====================================================================")
if DEBUG: print("Halted")
if DEBUG: print("=====================================================================")
display.halt()
    
