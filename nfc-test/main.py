from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.i2c import PN532_I2C
import RPi.GPIO as GPIO
import time
import asyncio
from typing import Optional

app = FastAPI(title="NFC Hex Reader/Writer API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

LED_PIN = 17  # GPIO pin connected to LED

# Initialize I2C communication and PN532
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

# Configure PN532
pn532.SAM_configuration()

# Get firmware version
ic, ver, rev, support = pn532.firmware_version
print(f"Found PN532 with firmware version: {ver}.{rev}")

# Request/Response models
class WriteHexRequest(BaseModel):
    hex_string: str

class ReadHexResponse(BaseModel):
    uid: str
    hex_data: str
    total_bytes: int
    successful_blocks: int
    message: str

class WriteHexResponse(BaseModel):
    uid: str
    hex_string: str
    total_bytes: int
    total_blocks: int
    message: str

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "NFC Hex Reader/Writer API", 
        "version": "1.0.0",
        "endpoints": {
            "read": "/read-pk",
            "write": "/write-pk"
        }
    }

@app.get("/read-pk", response_model=ReadHexResponse)
async def read_hex_from_nfc():
    """Read hex data from NFC tag"""
    try:
        print("Waiting for an NFC tag to read hex data...")
        
        # Wait for NFC tag with timeout
        start_time = time.time()
        timeout = 10  # 10 seconds timeout
        uid = None
        
        while time.time() - start_time < timeout:
            uid = pn532.read_passive_target(timeout=0.5)
            if uid:
                break
            await asyncio.sleep(0.1)
        
        if not uid:
            raise HTTPException(status_code=408, detail="Timeout: No NFC tag found within 10 seconds")
        
        print(f"Found NFC card with UID: {uid.hex().upper()}")
        GPIO.output(LED_PIN, GPIO.HIGH)
        
        # Read hex data from blocks starting at block 4
        read_data = bytearray()
        blocks_to_read = 16  # Read up to 64 bytes
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
                continue
        
        GPIO.output(LED_PIN, GPIO.LOW)
        
        if not read_data:
            raise HTTPException(status_code=404, detail="No data could be read from the tag")
        
        # Remove trailing null bytes (padding)
        while read_data and read_data[-1] == 0:
            read_data.pop()
        
        if not read_data:
            raise HTTPException(status_code=404, detail="No valid hex data found (all null bytes)")
        
        # Convert to hex string
        hex_string = read_data.hex()
        
        return ReadHexResponse(
            uid=uid.hex().upper(),
            hex_data=hex_string,
            total_bytes=len(read_data),
            successful_blocks=successful_reads,
            message="Hex data successfully read from NFC tag"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        GPIO.output(LED_PIN, GPIO.LOW)
        raise HTTPException(status_code=500, detail=f"Error reading NFC tag: {str(e)}")

@app.post("/write-pk", response_model=WriteHexResponse)
async def write_hex_to_nfc(request: WriteHexRequest):
    """Write hex data to NFC tag"""
    try:
        hex_string = request.hex_string.strip()
        
        # Validate input
        if not hex_string:
            raise HTTPException(status_code=400, detail="No hex string provided")
        
        print(f"Hex string to write: {hex_string}")
        print(f"Length: {len(hex_string)} characters")
        
        # Convert hex string to bytes
        try:
            data_bytes = bytes.fromhex(hex_string)
            print(f"Converted to {len(data_bytes)} bytes")
        except ValueError as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid hex string: {str(e)}. Please ensure the string contains only valid hexadecimal characters (0-9, a-f, A-F)"
            )
        
        # Ensure data is padded to a multiple of 4 bytes for NFC writing
        original_length = len(data_bytes)
        if len(data_bytes) % 4 != 0:
            padding = 4 - (len(data_bytes) % 4)
            data_bytes = data_bytes + (b'\x00' * padding)
            print(f"Padded to {len(data_bytes)} bytes with {padding} null bytes")
        
        print("Waiting for an NFC tag...")
        
        # Wait for NFC tag with timeout
        start_time = time.time()
        timeout = 10  # 10 seconds timeout
        uid = None
        
        while time.time() - start_time < timeout:
            uid = pn532.read_passive_target(timeout=0.5)
            if uid:
                break
            await asyncio.sleep(0.1)
        
        if not uid:
            raise HTTPException(status_code=408, detail="Timeout: No NFC tag found within 10 seconds")
        
        print(f"Found NFC card with UID: {uid.hex().upper()}")
        GPIO.output(LED_PIN, GPIO.HIGH)
        
        # Write in 4-byte chunks
        total_blocks = len(data_bytes) // 4
        print(f"Writing {len(data_bytes)} bytes in {total_blocks} blocks...")
        
        for i in range(0, len(data_bytes), 4):
            block_number = 4 + (i // 4)  # Start at block 4, increment every 4 bytes
            chunk = data_bytes[i:i+4]
            # Get the original hex string chunk (preserving case)
            start_pos = i * 2
            end_pos = (i + 4) * 2
            original_chunk = hex_string[start_pos:end_pos] if end_pos <= len(hex_string) else hex_string[start_pos:]
            print(f"Writing to block {block_number}: {original_chunk}")
            pn532.ntag2xx_write_block(block_number, chunk)
        
        GPIO.output(LED_PIN, GPIO.LOW)
        
        return WriteHexResponse(
            uid=uid.hex().upper(),
            hex_string=hex_string,
            total_bytes=original_length,
            total_blocks=total_blocks,
            message="Hex string successfully written to NFC tag"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        GPIO.output(LED_PIN, GPIO.LOW)
        raise HTTPException(status_code=500, detail=f"Error writing to NFC tag: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup GPIO on shutdown"""
    GPIO.cleanup()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
