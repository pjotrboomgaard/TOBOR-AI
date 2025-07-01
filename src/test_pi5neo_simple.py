#!/usr/bin/env python3
"""
Simple Pi5Neo test to verify SPI communication
"""

import spidev
import time

def test_pi5neo_manual():
    """Test Pi5Neo functionality by manually configuring SPI"""
    try:
        print("Testing Pi5Neo with manual SPI configuration...")
        
        # Create SPI device manually
        spi = spidev.SpiDev()
        spi.open(10, 0)  # Bus 10, Device 0
        spi.max_speed_hz = 800 * 1024 * 8  # 800kHz * 1024 * 8
        
        print("✓ SPI device opened successfully")
        
        # Test sending some data
        # This is a simple test pattern for 3 LEDs (RGB)
        test_data = []
        
        # LED 1: Red (GRB format)
        for color in [0, 255, 0]:  # Green=0, Red=255, Blue=0
            for bit in range(8):
                if color & (1 << (7 - bit)):
                    test_data.append(0xF8)  # High bit
                else:
                    test_data.append(0xC0)  # Low bit
        
        print(f"Sending test data: {len(test_data)} bytes")
        spi.xfer3(test_data)
        
        print("✓ Test data sent successfully")
        
        # Clear the strip
        clear_data = [0xC0] * (3 * 24)  # 3 LEDs * 24 bits each, all low
        spi.xfer3(clear_data)
        
        print("✓ Strip cleared")
        
        spi.close()
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Pi5Neo Manual SPI Test ===")
    success = test_pi5neo_manual()
    
    if success:
        print("\n✓ Manual SPI test successful - Pi5Neo should work with modification")
    else:
        print("\n✗ Manual SPI test failed - need to debug SPI communication") 