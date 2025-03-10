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

# Default keys for Mifare Classic authentication
# Many Mifare Classic cards use these default keys
DEFAULT_KEYS = [
    [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF],  # Factory default key
    [0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5],  # Common alternative key
    [0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7],  # Another common key
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]   # All zeros key
]

def read_ntag2xx(uid):
    """Read data from NTAG2xx tags (like NTAG213/215/216)"""
    print("Reading NTAG2xx tag...")
    
    # Read blocks starting from block 4 (first user writable block in most NTAG)
    num_blocks_to_read = 8
    all_data = bytearray()
    
    for block_number in range(4, 4 + num_blocks_to_read):
        try:
            block_data = pn532.ntag2xx_read_block(block_number)
            print(f"Block {block_number}: {block_data}")
            all_data.extend(block_data)
        except Exception as e:
            print(f"Error reading block {block_number}: {e}")
            break
    
    # Convert bytes to string and strip null bytes
    try:
        data_string = all_data.decode('ascii').rstrip('\x00')
        print(f"\nComplete data read: {data_string}")
    except UnicodeDecodeError:
        print(f"\nRaw data (not ASCII): {all_data}")

def read_mifare_classic(uid):
    """Read data from Mifare Classic cards"""
    print("Reading Mifare Classic card...")
    
    # Check card size based on UID
    if len(uid) == 4:
        # Mifare Classic 1K has 16 sectors with 4 blocks each
        num_sectors = 16
        print("Detected Mifare Classic 1K")
    elif len(uid) == 7:
        # Mifare Classic 4K has 40 sectors
        num_sectors = 40
        print("Detected Mifare Classic 4K")
    else:
        print(f"Unknown Mifare card type with UID length: {len(uid)}")
        num_sectors = 16  # Default to 1K
    
    all_data = []
    
    # Iterate through sectors
    for sector in range(num_sectors):
        print(f"\nSector {sector}:")
        
        # Determine block range for this sector
        if sector < 32:
            # First 32 sectors have 4 blocks each
            blocks_in_sector = 4
            first_block = sector * 4
        else:
            # Last 8 sectors have 16 blocks each (Mifare Classic 4K only)
            blocks_in_sector = 16
            first_block = 128 + (sector - 32) * 16
        
        # Try each key until one works for this sector
        authenticated = False
        key_used = None
        
        for key in DEFAULT_KEYS:
            try:
                # Try to authenticate with key A
                if pn532.mifare_classic_authenticate_block(
                    uid, first_block, 0x60, key):
                    authenticated = True
                    key_used = "A: " + " ".join([hex(k)[2:].zfill(2) for k in key])
                    break
            except Exception:
                pass
            
            try:
                # Try to authenticate with key B
                if pn532.mifare_classic_authenticate_block(
                    uid, first_block, 0x61, key):
                    authenticated = True
                    key_used = "B: " + " ".join([hex(k)[2:].zfill(2) for k in key])
                    break
            except Exception:
                pass
        
        if not authenticated:
            print(f"  Authentication failed for sector {sector}")
            continue
        
        print(f"  Authenticated with key {key_used}")
        
        # Read blocks in this sector (skip the sector trailer for safety)
        for i in range(blocks_in_sector - 1):
            block = first_block + i
            try:
                data = pn532.mifare_classic_read_block(block)
                hex_data = ' '.join([hex(b)[2:].zfill(2) for b in data])
                
                # Try to interpret as ASCII
                try:
                    ascii_data = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
                except:
                    ascii_data = "....."
                
                print(f"  Block {block}: {hex_data} | {ascii_data}")
                all_data.append((block, data, ascii_data))
            except Exception as e:
                print(f"  Error reading block {block}: {e}")

print("\nNFC Tag Reader")
print("Waiting for an NFC tag...")

while True:
    # Try to read a tag
    uid = pn532.read_passive_target(timeout=0.5)
    
    if uid:
        print(f"\nFound NFC card with UID: {uid.hex().upper()}")
        GPIO.output(LED_PIN, GPIO.HIGH)
        
        # Detect card type based on UID length and attempt to read
        if len(uid) == 7:
            # NTAG2xx typically has 7-byte UIDs
            read_ntag2xx(uid)
        elif len(uid) == 4 or len(uid) == 7:
            # Mifare Classic 1K has 4-byte UIDs, Mifare Classic 4K can have 7-byte UIDs
            read_mifare_classic(uid)
        else:
            print(f"Unknown card type with UID length: {len(uid)}")
        
        GPIO.output(LED_PIN, GPIO.LOW)
        print("\nRemove the tag to read another...")
        
        # Wait until tag is removed
        while pn532.read_passive_target(timeout=0.5):
            time.sleep(0.1)
            
        print("\nWaiting for next NFC tag...")
    
    time.sleep(0.1)  # Short delay to prevent CPU overuse