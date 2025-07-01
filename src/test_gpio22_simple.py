import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)      # Gebruik BCM-nummering
GPIO.setup(22, GPIO.OUT)    # Test GPIO 22

try:
    while True:
        # GPIO 22 AAN (actief LOW bij meeste relais)
        GPIO.output(22, GPIO.LOW)
        print("GPIO 22 AAN")
        time.sleep(2)               # 2 seconden aan

        # GPIO 22 UIT
        GPIO.output(22, GPIO.HIGH)
        print("GPIO 22 UIT")
        time.sleep(1)               # 1 seconde uit
        
except KeyboardInterrupt:
    print("\nGPIO 22 test gestopt")
finally:
    GPIO.cleanup() 