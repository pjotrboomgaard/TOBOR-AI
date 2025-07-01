#!/usr/bin/env python3
"""
Basic SPI test to check if SPI communication is working
"""

import spidev
import time

def test_spi():
    try:
        print("Testing SPI communication...")
        
        # Try to open SPI device
        spi = spidev.SpiDev()
        spi.open(10, 0)  # Bus 10, Device 0 (/dev/spidev10.0)
        
        print("✓ SPI device opened successfully")
        
        # Set SPI parameters
        spi.max_speed_hz = 8000000  # 8MHz
        spi.mode = 0
        
        print(f"✓ SPI configured: Speed={spi.max_speed_hz}Hz, Mode={spi.mode}")
        
        # Try to send some test data
        test_data = [0x00, 0xFF, 0xAA, 0x55]
        print(f"Sending test data: {[hex(x) for x in test_data]}")
        
        response = spi.xfer2(test_data)
        print(f"Received response: {[hex(x) for x in response]}")
        
        print("✓ SPI communication test completed successfully")
        
        spi.close()
        return True
        
    except Exception as e:
        print(f"✗ SPI test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Basic SPI Test ===")
    success = test_spi()
    
    if success:
        print("\n✓ SPI is working - LED strip should be able to communicate")
    else:
        print("\n✗ SPI is not working - need to fix SPI configuration first") 