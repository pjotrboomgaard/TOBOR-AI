import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)      # Gebruik BCM-nummering
GPIO.setup(26, GPIO.OUT)    # Test GPIO 26

try:
    while True:
        # GPIO 26 AAN (actief LOW bij meeste relais)
        GPIO.output(26, GPIO.LOW)
        print("GPIO 26 AAN")
        time.sleep(2)               # 2 seconden aan

        # GPIO 26 UIT
        GPIO.output(26, GPIO.HIGH)
        print("GPIO 26 UIT")
        time.sleep(1)               # 1 seconde uit
        
except KeyboardInterrupt:
    print("\nGPIO 26 test gestopt")
finally:
    GPIO.cleanup() 