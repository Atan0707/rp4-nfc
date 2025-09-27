import board
import busio
from digitalio import DigitalInOut
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

print("Waiting for an NFC tag to read hex data...")

while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid:
        print(f"Found NFC card with UID: {uid.hex().upper()}")
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.5)
        
        # Read hex data from blocks starting at block 4
        read_data = bytearray()
        
        try:
            # Read user data blocks directly (simplified for hex string reading)
            blocks_to_read = 16  # Read up to 64 bytes (16 blocks * 4 bytes each)
            successful_reads = 0
            
            print("Reading hex data blocks:")
            for block_num in range(4, 4 + blocks_to_read):
                try:
                    block_data = pn532.ntag2xx_read_block(block_num)
                    if block_data:
                        print(f"Block {block_num}: {block_data.hex()}")
                        read_data.extend(block_data)
                        successful_reads += 1
                        
                        # Check if we've hit all null bytes (end of data)
                        if block_data == b'\x00\x00\x00\x00':
                            print(f"Reached end of data at block {block_num}")
                            break
                    else:
                        print(f"Failed to read block {block_num} - returned None")
                        break
                except Exception as e:
                    print(f"Error reading block {block_num}: {e}")
                    # Try to continue reading other blocks
                    continue
            
            if read_data:
                # Remove trailing null bytes (padding)
                while read_data and read_data[-1] == 0:
                    read_data.pop()
                
                if read_data:
                    # Convert to hex string (preserving original case)
                    hex_string = read_data.hex()
                    
                    print(f"\n--- HEX DATA RESULTS ---")
                    print(f"Total bytes read: {len(read_data)}")
                    print(f"Successful block reads: {successful_reads}")
                    print(f"Original hex string: {hex_string}")
                    print(f"Hex string length: {len(hex_string)} characters")
                    
                else:
                    print("No valid hex data found (all null bytes)")
            else:
                print("No data could be read from the tag")
                
        except Exception as e:
            print(f"Error reading NFC tag: {e}")
        
        GPIO.output(LED_PIN, GPIO.LOW)
        print("\nRead complete! Remove the NFC tag.")
        
        # Wait for card to be removed before starting next cycle
        print("Waiting for card to be removed...")
        while True:
            check_uid = pn532.read_passive_target(timeout=0.5)
            if not check_uid:
                print("Card removed! Ready for next tag.")
                time.sleep(1)  # Brief pause before starting next cycle
                break
            time.sleep(0.2)  # Small delay before checking again
