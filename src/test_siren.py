import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)      # Gebruik BCM-nummering
GPIO.setup(4, GPIO.OUT)     # Zwaailicht op GPIO 4

try:
    while True:
        # Zwaailicht AAN (actief LOW bij meeste relais)
        GPIO.output(4, GPIO.LOW)
        print("Zwaailicht AAN")
        time.sleep(2)               # 2 seconden aan

        # Zwaailicht UIT
        GPIO.output(4, GPIO.HIGH)
        print("Zwaailicht UIT")
        time.sleep(1)               # 1 seconde uit
        
except KeyboardInterrupt:
    print("\nSiren test gestopt")
finally:
    GPIO.cleanup() 