import RPi.GPIO as GPIO
import time

# Relay shield pins
SIREN_PIN = 4    # Known - siren
TEST_PINS = [22, 6, 26]  # Unknown - eyes, mouth, LED

GPIO.setmode(GPIO.BCM)

# Setup all pins as outputs
GPIO.setup(SIREN_PIN, GPIO.OUT)
for pin in TEST_PINS:
    GPIO.setup(pin, GPIO.OUT)

# Start with all relays OFF (HIGH = OFF for active low relays)
GPIO.output(SIREN_PIN, GPIO.HIGH)
for pin in TEST_PINS:
    GPIO.output(pin, GPIO.HIGH)

print("=" * 50)
print("RELAY SHIELD PIN IDENTIFICATION TEST")
print("=" * 50)
print("Known: GPIO 4 = Siren")
print("Testing: GPIO 22, 6, 26 (eyes, mouth, LED)")
print("=" * 50)

try:
    for i, pin in enumerate(TEST_PINS, 1):
        print(f"\n🔹 TEST {i}/3: Testing GPIO pin {pin}")
        print(f"   Turning ON GPIO {pin} for 10 seconds...")
        print(f"   Watch your hardware - what turned on?")
        print("   (Eyes, Mouth lights, or other LED)")
        
        # Turn ON this pin (LOW = ON for active low relay)
        GPIO.output(pin, GPIO.LOW)
        
        # Countdown timer
        for seconds in range(10, 0, -1):
            print(f"   ⏰ {seconds} seconds remaining...", end="\r")
            time.sleep(1)
        
        # Turn OFF this pin
        GPIO.output(pin, GPIO.HIGH)
        print(f"\n   ✅ GPIO {pin} test complete - turned OFF")
        
        if i < len(TEST_PINS):
            print("   Waiting 2 seconds before next test...")
            time.sleep(2)

    print("\n" + "=" * 50)
    print("🎯 PIN IDENTIFICATION COMPLETE!")
    print("=" * 50)
    print("Please note which hardware was controlled by each pin:")
    print("• GPIO 22 controlled: ____________")
    print("• GPIO 6  controlled: ____________") 
    print("• GPIO 26 controlled: ____________")
    print("=" * 50)

except KeyboardInterrupt:
    print("\n❌ Test interrupted by user")
    
finally:
    # Make sure all pins are OFF before cleanup
    GPIO.output(SIREN_PIN, GPIO.HIGH)
    for pin in TEST_PINS:
        GPIO.output(pin, GPIO.HIGH)
    
    GPIO.cleanup()
    print("🧹 GPIO cleanup complete") 