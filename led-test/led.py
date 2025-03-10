import RPi.GPIO as GPIO
import time

LED_PIN = 17  # GPIO pin number

GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbering
GPIO.setup(LED_PIN, GPIO.OUT)  # Set pin as output

try:
    while True:
        GPIO.output(LED_PIN, GPIO.HIGH)  # Turn LED on
        print("LED ON")
        time.sleep(1)  # Wait 1 second

        GPIO.output(LED_PIN, GPIO.LOW)  # Turn LED off
        print("LED OFF")
        time.sleep(1)  # Wait 1 second

except KeyboardInterrupt:
    GPIO.cleanup()  # Reset GPIO settings
    print("\nGPIO Cleaned up, exiting...")