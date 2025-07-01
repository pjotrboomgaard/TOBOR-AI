import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)      # Gebruik BCM-nummering
GPIO.setup(6, GPIO.OUT)     # Test GPIO 6

try:
    while True:
        # GPIO 6 AAN (actief LOW bij meeste relais)
        GPIO.output(6, GPIO.LOW)
        print("GPIO 6 AAN")
        time.sleep(2)               # 2 seconden aan

        # GPIO 6 UIT
        GPIO.output(6, GPIO.HIGH)
        print("GPIO 6 UIT")
        time.sleep(1)               # 1 seconde uit
        
except KeyboardInterrupt:
    print("\nGPIO 6 test gestopt")
finally:
    GPIO.cleanup() 