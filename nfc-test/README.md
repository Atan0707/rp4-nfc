# NFC Test Project

This project provides Python scripts to read from and write to NFC tags using a PN532 NFC module connected to a Raspberry Pi. The project includes support for both NTAG2xx tags (like NTAG213/215/216) and Mifare Classic cards.

## Hardware Requirements

- Raspberry Pi (any model with I2C support)
- PN532 NFC/RFID Module
- LED (optional, for visual feedback)
- 220Ω resistor (for LED)
- Breadboard and jumper wires
- NFC tags (NTAG213/215/216 or Mifare Classic 1K/4K)

## Hardware Connections

### PN532 Module to Raspberry Pi (I2C)
- VCC → 3.3V (Pin 1)
- GND → Ground (Pin 6)
- SDA → GPIO 2 (Pin 3)
- SCL → GPIO 3 (Pin 5)

### LED (Optional)
- LED Anode → GPIO 17 (Pin 11) through 220Ω resistor
- LED Cathode → Ground

## Software Setup

### 1. Enable I2C on Raspberry Pi
```bash
sudo raspi-config
```
Navigate to "Interfacing Options" → "I2C" → "Yes" to enable I2C.

### 2. Install System Dependencies
```bash
sudo apt update
sudo apt install python3-pip python3-dev python3-venv i2c-tools
```

### 3. Verify I2C Connection
```bash
sudo i2cdetect -y 1
```
You should see the PN532 module at address 0x24.

### 4. Create Virtual Environment (Recommended)
```bash
python3 -m venv nfc-env
source nfc-env/bin/activate
```

### 5. Install Python Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Reading NFC Tags (`read.py`)

This script can read both NTAG2xx and Mifare Classic cards automatically:

```bash
python3 read.py
```

**Features:**
- Automatic card type detection
- Support for NTAG213/215/216 tags
- Support for Mifare Classic 1K and 4K cards
- Multiple authentication key attempts for Mifare Classic
- LED feedback when a tag is detected
- Hexadecimal and ASCII data display

**Supported Cards:**
- **NTAG2xx**: Reads user data blocks (blocks 4-11)
- **Mifare Classic**: Attempts to read all sectors using common default keys

### Writing to NFC Tags (`write.py`)

This script writes data to NTAG2xx tags:

```bash
python3 write.py
```

**Features:**
- Writes "Hello, NFC Tag!" to NTAG2xx tags
- Automatic 4-byte block alignment
- LED feedback during write operation
- Starts writing from block 4 (first user-writable block)

**To modify the data:**
Edit the `data_to_write` variable in `write.py`:
```python
data_to_write = "Your custom message here"
```

## File Structure

```
nfc-test/
├── read.py           # NFC tag reader script
├── write.py          # NFC tag writer script
├── requirements.txt  # Python dependencies
└── README.md        # This documentation
```

## Troubleshooting

### Common Issues

1. **"No I2C device found"**
   - Check wiring connections
   - Ensure I2C is enabled: `sudo raspi-config`
   - Verify with: `sudo i2cdetect -y 1`

2. **"Permission denied" errors**
   - Run with sudo: `sudo python3 read.py`
   - Or add user to gpio group: `sudo usermod -a -G gpio $USER`

3. **"Module not found" errors**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

4. **"Authentication failed" for Mifare Classic**
   - The card may use non-default keys
   - Some sectors may be protected
   - This is normal for used/programmed cards

5. **LED not working**
   - Check LED polarity (longer leg = anode)
   - Verify GPIO 17 connection
   - Check resistor value (220Ω recommended)

### Default Mifare Classic Keys

The reader tries these common keys:
- `FF FF FF FF FF FF` (Factory default)
- `A0 A1 A2 A3 A4 A5` (Common alternative)
- `D3 F7 D3 F7 D3 F7` (Another common key)
- `00 00 00 00 00 00` (All zeros)

## Safety Notes

- The write script only writes to NTAG2xx tags (safer for testing)
- Mifare Classic writing is not implemented to prevent accidental damage
- Always test with disposable tags first
- Some NFC tags have write-protection features

## Supported Tag Types

### NTAG2xx Family
- **NTAG213**: 180 bytes user memory
- **NTAG215**: 540 bytes user memory  
- **NTAG216**: 924 bytes user memory

### Mifare Classic Family
- **Mifare Classic 1K**: 1024 bytes total (768 bytes user memory)
- **Mifare Classic 4K**: 4096 bytes total (3440 bytes user memory)

## License

This project is provided as-is for educational and testing purposes.

## Contributing

Feel free to submit issues and enhancement requests!