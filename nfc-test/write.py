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

data_to_write = "Hello, NFC Tag!"  # 16 bytes
# Convert string to bytes
data_bytes = data_to_write.encode('ascii')

# Ensure data is padded to a multiple of 4 bytes
if len(data_bytes) % 4 != 0:
    padding = 4 - (len(data_bytes) % 4)
    data_bytes = data_bytes + (b'\x00' * padding)

print("Waiting for an NFC tag...")

while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid:
        print(f"Found NFC card with UID: {uid.hex().upper()}")
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(1)

        # Write in 4-byte chunks
        for i in range(0, len(data_bytes), 4):
            block_number = 4 + (i // 4)  # Start at block 4, increment every 4 bytes
            chunk = data_bytes[i:i+4]
            print(f"Writing to block {block_number}: {chunk}")
            pn532.ntag2xx_write_block(block_number, chunk)

        print("Write successful! Remove the NFC tag.")
        GPIO.output(LED_PIN, GPIO.LOW)
        
        # Wait for card to be removed before starting next cycle
        print("Waiting for card to be removed...")
        while True:
            check_uid = pn532.read_passive_target(timeout=0.5)
            if not check_uid:
                print("Card removed! Ready for next tag.")
                time.sleep(1)  # Brief pause before starting next cycle
                break
            time.sleep(0.2)  # Small delay before checking again