from machine import Pin, ADC, I2C
from pico_i2c_lcd import I2cLcd
from lcd_api import LcdApi
from time import sleep, ticks_ms, ticks_diff
from imu import MPU6050
import math
import network
import urequests
import _thread

ssid = '###'     # SSID of the Wi-Fi network
password = '###'            # Password 

# Replace the ThingSpeak configuration with:
SERVER_URL = 'http://192.168.1.1:3000/api/sensor'  # Replace YOUR_COMPUTER_IP

# Set up Wi-Fi in station mode

wlan = network.WLAN(network.STA_IF)  # Create a WLAN object in station mode, the device connects to a Wi-Fi network as a client. 
wlan.active(True)                    # Activate the Wi-Fi interface
wlan.connect(ssid, password)         # Connect to the specified Wi-Fi network

# Wait until connected

print("Connecting to Wi-Fi...", end="")

while not wlan.isconnected():
    print(".", end="")               # Print dots while waiting
    sleep(0.5)                  # Wait half a second before retrying

# Once connected, print confirmation and IP address

print("\nConnected!")
print("IP address:", wlan.ifconfig()[0])  # Display the assigned IP address


# Initialize pins 
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000) # I2C bus 1, SDA pin 0, SCL pin 1, 400kHz
i2c1 = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)  # I2C bus 2, SDA pin 14, SCL pin 15, 400kHz
lcd = I2cLcd(i2c, 0x27, 2, 16)
button = Pin(19, Pin.IN, Pin.PULL_DOWN)

mpu = MPU6050(i2c1)
pot = ADC(Pin(26))
led_green = Pin(3, Pin.OUT)
led_yellow = Pin(4, Pin.OUT)
led_red = Pin(5, Pin.OUT)


sampleAmount = 3 # samples for measure average
degConvert = 0.000657 #range 43 cm, 43/65535 = 0.000657

# Global flag for remote trigger
remote_trigger_flag = False
trigger_check_interval = 1000  # Check every 1 second
last_trigger_check = 0

# Function to send data to endpoint
def send_to_endpoint(measure, angle):
    try:
        # Send HTTP POST request to your local server
        url = '{}?measure_cm={}&angle={}'.format(SERVER_URL, measure, angle)
        response = urequests.post(url)
        print("Server response:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data:", e)

# Function to turn off all LEDs
def allLedOff():
    led_green.off()
    led_red.off()
    led_yellow.off()
    return None

# Asynchronous function to check for remote trigger in background thread
def trigger_checker_thread():
    global remote_trigger_flag
    while True:
        try:
            response = urequests.get(SERVER_URL.replace('/api/sensor', '/api/check-trigger'))
            data = response.json()
            response.close()
            if data.get('trigger', False):
                remote_trigger_flag = True
                print("Remote trigger received!")
        except Exception as e:
            pass  # Silently handle errors in background
        sleep(1)  # Check every second

# Start background thread for trigger checking
_thread.start_new_thread(trigger_checker_thread, ())

# Main loop

while True:
    potValue = pot.read_u16() # read value, 0-65535 across voltage range 0.0v - 3.3v
    print(potValue)
    
    avgData = 0 # resets avgData

    # Gathers saples for avegering data
    for data in range(sampleAmount):
        avgData += potValue

    avgData /= sampleAmount
    degValue = (avgData * degConvert) # Converts read value to degrees (range 43 cm, 43/65535 = 0.000657)
    print(int(degValue))
    
    # Collects data from mpu
    xAccel=mpu.accel.x
    yAccel=mpu.accel.y
    zAccel=mpu.accel.z
    
    # Calculate pitch
    pitch=math.atan(yAccel/zAccel)
    pitchDeg=pitch/(2*math.pi)*360
    print('pitch: ',pitchDeg)
    
    # Converts pitch to integer and absolute value
    displayDeg = abs(int(pitchDeg))
    
    # Controls leds for angle
    if 15 >= displayDeg >= -15:
        led_red.on()
    if 5 >= displayDeg >= -5:
        led_yellow.on()
    if 1 >= displayDeg >= -1:
        led_green.on()
    
    # Check for physical button press OR remote trigger flag
    if button.value() == 1 or remote_trigger_flag:
        try:
            sendDegValue = int(degValue)
            print("Measurement triggered! Sending data...")
            send_to_endpoint(sendDegValue, displayDeg)  # Send distance and angle
            remote_trigger_flag = False  # Reset flag after sending
        except Exception as e:
            print("Error:", e)
    
    # LCD output
    lcdValue = int(degValue)
    lcd.clear()
    lcd.putstr(f"Measure: {lcdValue} cm")
    lcd.move_to(0, 1)
    lcd.putstr(f"Degrees: {displayDeg}")
    sleep(0.5)
    allLedOff()

