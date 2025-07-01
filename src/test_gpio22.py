import RPi.GPIO as GPIO
import time

# Test only GPIO pin 22
TEST_PIN = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(TEST_PIN, GPIO.OUT)

# Start with relay OFF (HIGH = OFF for active low relays)
GPIO.output(TEST_PIN, GPIO.HIGH)

print("=" * 50)
print("FOCUSED GPIO PIN 22 TEST")
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
        print(f"   ⏰ {seconds} seconds remaining - GPIO {TEST_PIN} is ON", end="\r")
        time.sleep(1)
    
    print(f"\n   🔹 Turning GPIO {TEST_PIN} OFF...")
    GPIO.output(TEST_PIN, GPIO.HIGH)
    print(f"   📍 GPIO {TEST_PIN} is now OFF (HIGH signal)")
    
    print("\n" + "=" * 50)
    print("🎯 GPIO 22 TEST COMPLETE!")
    print("=" * 50)
    print("Did you see ANY hardware activate?")
    print("• Lights turning on/off?")
    print("• Motors moving?") 
    print("• LEDs blinking?")
    print("• Any other devices?")
    print("=" * 50)

except KeyboardInterrupt:
    print("\n❌ Test interrupted by user")
    
finally:
    # Make sure pin is OFF before cleanup
    GPIO.output(TEST_PIN, GPIO.HIGH)
    GPIO.cleanup()
    print("🧹 GPIO cleanup complete") 