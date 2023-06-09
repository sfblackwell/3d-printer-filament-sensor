# Yet another 3d printer filament humidity sensor using a Pimoroni Badger W with a BME280 sensor.

## This project is an educational tool, mainly for ME :)

## This version uses the Badger specific @Micropython UF2

- Now using the Badger OS functions to implement sleep & wake up
  - https://github.com/pimoroni/badger2040/blob/main/docs/reference.md#button-presses
  - https://github.com/pimoroni/badger2040/blob/main/docs/reference.md#real-time-clock
  - Hopefully this will lower battery consumption when halted
  - Wake method (O = Other, B = Button, R = RTC timer trigger) is displayed on top line along with WiFi (C = Connected) status  
- As always has a load of debug messages that can be toggled on or off

### Overview

- Reads humidity and temperature based on parameters using the BME280
  - Currenty every 30 mins 
  - Most parameters are ajustable in paramters.json file 
- Logs readings to MariaDB using a simple REST interface
  - Humidity
  - Temperature
  - Power source (USB or Battery)
  - Power Level in Volts
  - Parameters for 'Full', 'Empty' and Change Battery'
  - See images for graphs created using logged data    
- Sends emails for:
  - Out of bounds humidity readings 
  - Battery level and change warnings
  - uses the [umail](https://github.com/shawwwn/uMail) class by https://github.com/shawwwn
- At end of run puts device in to deep power saving sleep until retriggered by button or the RTC
  - now using Badger OS functions (pcf85063a) to implement RTC wake up
-   Now implements badger2040.sleep_for(minutes) rather than Pico machine.deepsleep
  
The [netmanClass.py](https://github.com/sfblackwell/3d-printer-filament-sensor/blob/e0c5dca9e58f53612bed2ad16eb20dea8897b15f/python-code/lib/netmanClass.py) contains a simple WiFI connection class and methods for reading power source and levels. They are contained within the Wifi class as power source and power levels use some common GPIO functions. 

The code contains a lot of DEBUG print statments to REPL that can be enabled / disabled at start of code.

### *** This is a work in progress ***

### *** I am not a coder or programer, so please excuse the chaos ***

### Items Used:

- Processor [Pimoroni Badger 2040 W](https://shop.pimoroni.com/products/badger-2040-w?variant=40514062221395)
- I2C Sensor [Pimoroni BME280 Breakout - Temperature, Pressure, Humidity Sensor](https://shop.pimoroni.com/products/bme280-breakout)
- Battery Pack [Battery Holder 3xAA with Cover and Switch - JST Connector](https://shop.pimoroni.com/products/battery-holder-3xaa-with-cover-and-switch-jst-connector)
- Micropython [pimoroni-badger2040w-v1.19.16-micropython-with-examples.uf2
](https://github.com/pimoroni/pimoroni-pico/releases/download/v1.19.16/pimoroni-badger2040w-v1.19.16-micropython-with-examples.uf2)
- Case [Badger2040 Enclosure 3d Printed Case ](https://www.printables.com/model/145686-badger2040-enclosure/comments)
- Web HTML graphing [Apex Charts with PHP and Javascript](https://apexcharts.com/)
- Micropython eMail Alerts [umail](https://github.com/shawwwn/uMail) class by https://github.com/shawwwn


A picture: 

![20230320_085055608_iOS](https://user-images.githubusercontent.com/122044826/227652855-81abf171-3f7c-4957-a381-bec39fc60271.jpg)

Graphing output on web, red is out of bounds alert:

![Screenshot 2023-03-24 225020](https://user-images.githubusercontent.com/122044826/227657046-52d38811-8f88-43d0-a58e-491e571438a6.jpg)
