import RPi.GPIO as GPIO
import time

# Test only GPIO pin 6
TEST_PIN = 6

GPIO.setmode(GPIO.BCM)
GPIO.setup(TEST_PIN, GPIO.OUT)

# Start with relay OFF (HIGH = OFF for active low relays)
GPIO.output(TEST_PIN, GPIO.HIGH)

print("=" * 50)
print("FOCUSED GPIO PIN 6 TEST")
print("=" * 50)
print(f"Testing ONLY GPIO pin {TEST_PIN}")
print("Watch for ANY hardware activation!")
print("=" * 50)

try:
    print(f"\n🔹 Turning GPIO {TEST_PIN} ON...")
    print("   Watch carefully for ANY lights, motors, or devices!")
    
    # Turn ON (LOW = ON for active low relay)
    GPIO.output(TEST_PIN, GPIO.LOW)
    print(f"   📍 GPIO {TEST_PIN} is now ON (LOW signal)")
    
    # Keep it on for 30 seconds with countdown
    for seconds in range(30, 0, -1):
        print(f"   ⏰ {seconds} seconds remaining - GPIO {TEST_PIN} ON")
        time.sleep(1)
    
    print(f"\n🔹 Turning GPIO {TEST_PIN} OFF...")
    # Turn OFF (HIGH = OFF for active low relay)
    GPIO.output(TEST_PIN, GPIO.HIGH)
    print(f"   📍 GPIO {TEST_PIN} is now OFF (HIGH signal)")
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE!")
    print("=" * 50)
    print(f"What did you observe when GPIO {TEST_PIN} was ON?")
    print("- Eyes?")
    print("- Mouth?") 
    print("- Other LED?")
    print("- Nothing?")
    print("=" * 50)
    
except KeyboardInterrupt:
    print(f"\n\nTest interrupted!")
finally:
    GPIO.output(TEST_PIN, GPIO.HIGH)  # Ensure OFF
    GPIO.cleanup()
    print("GPIO cleanup complete.") 