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

print("Waiting for an NFC tag to read...")

while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid:
        print(f"Found NFC card with UID: {uid.hex().upper()}")
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.5)
        
        # Read data from blocks starting at block 4
        # Assuming the data was written in the same format as write.py
        read_data = bytearray()
        
        try:
            # Read multiple blocks to get the full message
            # Start from block 4 and read enough blocks to get the full message
            for block_num in range(4, 8):  # Read blocks 4-7 (16 bytes total)
                try:
                    block_data = pn532.ntag2xx_read_block(block_num)
                    if block_data:
                        print(f"Block {block_num}: {block_data.hex()} -> {block_data}")
                        read_data.extend(block_data)
                    else:
                        print(f"Failed to read block {block_num}")
                        break
                except Exception as e:
                    print(f"Error reading block {block_num}: {e}")
                    break
            
            if read_data:
                # Remove null padding and convert to string
                # Find the first null byte and truncate there
                null_index = read_data.find(b'\x00')
                if null_index != -1:
                    clean_data = read_data[:null_index]
                else:
                    clean_data = read_data
                
                try:
                    decoded_message = clean_data.decode('ascii')
                    print(f"Decoded message: '{decoded_message}'")
                except UnicodeDecodeError:
                    print(f"Raw data (couldn't decode as ASCII): {clean_data}")
                
                print(f"Total bytes read: {len(read_data)}")
                print(f"Raw data: {read_data.hex()}")
            else:
                print("No data could be read from the tag")
                
        except Exception as e:
            print(f"Error reading NFC tag: {e}")
        
        GPIO.output(LED_PIN, GPIO.LOW)
        print("Read complete! Remove the NFC tag.")
        time.sleep(2)  # Wait before reading again
