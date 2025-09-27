import board
import busio
from adafruit_pn532.i2c import PN532_I2C
import RPi.GPIO as GPIO
import time

LED_PIN = 17  # GPIO pin connected to LED

# Initialize I2C communication
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)

GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbering
GPIO.setup(LED_PIN, GPIO.OUT)  # Set pin as output

# Get firmware version
ic, ver, rev, support = pn532.firmware_version
print(f"Found PN532 with firmware version: {ver}.{rev}")

# Configure PN532 to read RFID/NFC tags
pn532.SAM_configuration()

print("Waiting for an NFC tag to analyze...")

while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid:
        print(f"\n=== NFC TAG INFORMATION ===")
        print(f"UID: {uid.hex().upper()}")
        print(f"UID Length: {len(uid)} bytes")
        
        GPIO.output(LED_PIN, GPIO.HIGH)
        
        # Determine likely tag type based on UID length
        if len(uid) == 4:
            print("Likely tag type: Mifare Classic 1K")
        elif len(uid) == 7:
            print("Likely tag type: NTAG2xx or Mifare Classic 4K")
        else:
            print(f"Unknown tag type (UID length: {len(uid)})")
        
        # Try to read different blocks to understand the tag structure
        print("\n=== ATTEMPTING TO READ BLOCKS ===")
        
        # Try reading block 0 (header)
        try:
            block0 = pn532.ntag2xx_read_block(0)
            if block0:
                print(f"Block 0 (header): {block0.hex().upper()}")
                # Analyze the header
                if block0[0:3] == uid[0:3]:
                    print("  ✓ Block 0 contains UID - likely NTAG2xx")
                else:
                    print("  ? Block 0 structure unclear")
            else:
                print("Block 0: Failed to read")
        except Exception as e:
            print(f"Block 0: Error - {e}")
        
        # Try reading blocks 1-3 (system blocks)
        for block_num in [1, 2, 3]:
            try:
                block_data = pn532.ntag2xx_read_block(block_num)
                if block_data:
                    print(f"Block {block_num}: {block_data.hex().upper()}")
                else:
                    print(f"Block {block_num}: Failed to read")
            except Exception as e:
                print(f"Block {block_num}: Error - {e}")
        
        # Try reading user data blocks (4-10)
        print("\n=== USER DATA BLOCKS ===")
        for block_num in range(4, 11):
            try:
                block_data = pn532.ntag2xx_read_block(block_num)
                if block_data:
                    hex_data = block_data.hex().upper()
                    # Check if block contains any non-zero data
                    if any(b != 0 for b in block_data):
                        print(f"Block {block_num}: {hex_data} (contains data)")
                    else:
                        print(f"Block {block_num}: {hex_data} (empty)")
                else:
                    print(f"Block {block_num}: Failed to read")
                    break
            except Exception as e:
                print(f"Block {block_num}: Error - {e}")
                break
        
        GPIO.output(LED_PIN, GPIO.LOW)
        print(f"\n=== ANALYSIS COMPLETE ===")
        print("Remove the tag to analyze another one...")
        
        # Wait for tag removal
        while True:
            check_uid = pn532.read_passive_target(timeout=0.5)
            if not check_uid:
                break
            time.sleep(0.2)
        
        print("\nWaiting for next tag...")
        time.sleep(1)
