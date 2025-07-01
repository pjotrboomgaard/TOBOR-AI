#!/usr/bin/env python3
"""
SPI Pin Diagnostic - Send test signals to verify GPIO 10 (MOSI) is working
"""

import spidev
import time

def test_spi_output():
    """Send continuous test patterns to SPI to verify pin output"""
    try:
        print("Testing SPI output on GPIO 10 (MOSI)...")
        print("Connect a multimeter or LED+resistor to GPIO 10 to verify signal")
        
        spi = spidev.SpiDev()
        spi.open(10, 0)  # Bus 10, Device 0
        spi.max_speed_hz = 800000  # 800kHz
        
        print("✓ SPI device opened")
        print("Sending test patterns for 30 seconds...")
        print("You should see voltage changes on GPIO 10 (Pin 19)")
        
        start_time = time.time()
        while time.time() - start_time < 30:
            # Send alternating high/low pattern
            high_pattern = [0xFF] * 100  # All high bits
            low_pattern = [0x00] * 100   # All low bits
            
            spi.xfer3(high_pattern)
            time.sleep(0.1)
            spi.xfer3(low_pattern)
            time.sleep(0.1)
            
            print(".", end="", flush=True)
        
        print("\nTest completed!")
        spi.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== SPI Pin Diagnostic ===")
    print("This will send signals to GPIO 10 (Pin 19 - MOSI)")
    print("Use a multimeter to check if you see voltage changes")
    print("Expected: 0V to 3.3V switching")
    print()
    
    input("Press Enter to start test (Ctrl+C to stop)...")
    test_spi_output() 