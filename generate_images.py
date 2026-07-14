from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib
import textwrap

base = Path('static/images')
base.mkdir(parents=True, exist_ok=True)

products = [
    ('Arduino Uno R3', 'arduino-uno-r3.jpg'),
    ('Arduino Nano', 'arduino-nano.jpg'),
    ('Arduino Mega 2560', 'arduino-mega-2560.jpg'),
    ('ESP32 DevKit', 'esp32-devkit.jpg'),
    ('ESP8266 NodeMCU', 'esp8266-nodemcu.jpg'),
    ('Breadboard 830', 'breadboard-830.jpg'),
    ('Breadboard Power Module', 'mb102-power-module.jpg'),
    ('Jumper Wire (120 ც.)', 'jumper-wires.jpg'),
    ('SG90 Servo Motor', 'sg90-servo.jpg'),
    ('MG996R Servo', 'mg996r-servo.jpg'),
    ('DC Gear Motor TT', 'tt-gear-motor.jpg'),
    ('Stepper Motor 28BYJ-48', '28byj48.jpg'),
    ('ULN2003 Driver', 'uln2003.jpg'),
    ('L298N Motor Driver', 'l298n.jpg'),
    ('HC-SR04 Ultrasonic', 'hc-sr04.jpg'),
    ('DHT11', 'dht11.jpg'),
    ('PIR Motion Sensor', 'pir-sensor.jpg'),
    ('Flame Sensor', 'flame-sensor.jpg'),
    ('Rain Sensor', 'rain-sensor.jpg'),
    ('Soil Moisture Sensor', 'soil-moisture.jpg'),
    ('RFID RC522', 'rc522.jpg'),
    ('Bluetooth HC-05', 'hc05.jpg'),
    ('Relay Module 1 Channel', 'relay-1ch.jpg'),
    ('LCD 1602 I2C', 'lcd1602-i2c.jpg'),
    ('OLED Display 0.96"', 'oled096.jpg'),
    ('Joystick Module', 'joystick.jpg'),
    ('Sound Sensor', 'sound-sensor.jpg'),
    ('Buzzer Module', 'buzzer.jpg'),
    ('Push Button', 'push-button.jpg'),
    ('Potentiometer 10K', 'potentiometer-10k.jpg'),
]

try:
    font = ImageFont.truetype('arial.ttf', 28)
except Exception:
    font = ImageFont.load_default()

for name, filename in products:
    out = base / filename
    if out.exists():
        continue
    img = Image.new('RGB', (900, 600), (12, 20, 36))
    draw = ImageDraw.Draw(img)
    digest = hashlib.md5(name.encode()).digest()
    accent = ((digest[0] % 180) + 60, (digest[1] % 180) + 60, (digest[2] % 180) + 60)

    for i in range(8):
        draw.rectangle((40 + i * 90, 30 + i * 15, 860 - i * 90, 570 - i * 15), outline=accent, width=2)
    draw.rectangle((50, 50, 850, 550), outline=(255, 255, 255), width=3)

    lines = textwrap.wrap(name, width=18)
    y = 240
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((900 - w) // 2, y), line, fill=(255, 255, 255), font=font)
        y += 36

    draw.text((70, 510), 'Skema', fill=(220, 220, 220), font=font)
    img.save(out, format='JPEG', quality=92)

print(f'Generated {len(list(base.glob("*")))} images in {base}')
