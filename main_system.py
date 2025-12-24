# ================== IMPORT ==================
import I2C_LCD_driver
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from time import sleep
import RPi.GPIO as GPIO

from flask import Flask, render_template_string
import threading

# ================== GPIO ==================
button = 17
relay = 27
motorstatus = True

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(relay, GPIO.OUT, initial=GPIO.LOW)

# ================== LCD ==================
lcd = I2C_LCD_driver.lcd()
lcd.lcd_display_string("System Loading", 1, 0)
for a in range(16):
    lcd.lcd_display_string(".", 2, a)
    sleep(0.1)
lcd.lcd_clear()
lcd.lcd_display_string("Motor   :OFF", 2, 0)

# ================== ADS1115 ==================
i2c = busio.I2C(board.SCL, board.SDA, frequency=100_000)
ads = ADS.ADS1115(i2c)
ads.gain = 1
chan = AnalogIn(ads, 0)

# ================== FLASK ==================
app = Flask(__name__)

latest_data = {
    "moisture": "--",
    "voltage": "--",
    "motor": "OFF"
}


HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Irrigation</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #f1c40f, #f39c12);
            color: #2c3e50;
        }

        .container {
            max-width: 420px;
            margin: auto;
            padding: 15px;
        }

        .header {
            display: flex;
            align-items: center;
            gap: 14px;
            color: white;
            margin-bottom: 20px;
        }

        .header img {
            width: 80px;
            height: 80px;
            border-radius: 16px;
            background: white;
            padding: 6px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.25);
        }

        .header-text h2 {
            margin: 0;
            font-size: 22px;
        }

        .header-text h4 {
            margin: 4px 0;
            font-weight: normal;
        }

        .header-text p {
            margin: 0;
            font-size: 13px;
            opacity: 0.9;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 18px;
            margin-bottom: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }

        .title {
            font-size: 14px;
            text-transform: uppercase;
            color: #7f8c8d;
            margin-bottom: 5px;
        }

        .value {
            font-size: 28px;
            font-weight: bold;
        }

        .mode {
            font-weight: bold;
            padding: 8px 14px;
            border-radius: 20px;
            color: white;
            display: inline-block;
        }

        .auto { background: #e67e22; }
        .manual { background: #27ae60; }

        .btn {
            width: 100%;
            padding: 14px;
            margin-top: 10px;
            font-size: 16px;
            border-radius: 12px;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }

        .btn-auto { background: #2ecc71; color: white; }
        .btn-manual { background: #f39c12; color: white; }

        .btn-on { background: #27ae60; color: white; }
        .btn-off { background: #c0392b; color: white; }

        .progress {
            background: #ecf0f1;
            border-radius: 20px;
            overflow: hidden;
            height: 20px;
            margin-top: 10px;
        }

        .progress-bar {
            height: 100%;
            width: {{ moisture }}%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
        }

        footer {
            text-align: center;
            color: white;
            font-size: 12px;
            opacity: 0.85;
            margin-top: 10px;
        }
    </style>
</head>

<body>
<div class="container">

    <div class="header">
        <img src="/static/logo.png" alt="Logo">
        <div class="header-text">
            <h2>Smart Irrigation System</h2>
            <h4>Kelompok 3</h4>
            <p>Sistem Penyiraman Otomatis</p>
        </div>
    </div>

    <div class="card">
        <div class="title">Mode Sistem</div>
        <div class="value">
            <span class="mode {{ 'auto' if mode=='AUTO' else 'manual' }}">{{ mode }}</span>
        </div>

        <form method="post" action="/mode">
            <button class="btn btn-auto" name="mode" value="AUTO">AUTO</button>
            <button class="btn btn-manual" name="mode" value="MANUAL">MANUAL</button>
        </form>
    </div>

    <div class="card">
        <div class="title">Kelembapan Tanah</div>
        <div class="value">{{ moisture }} %</div>

        <div class="progress">
            <div class="progress-bar"></div>
        </div>

        <p style="margin-top:8px">Tegangan Sensor: {{ voltage }} V</p>
    </div>

    <div class="card">
        <div class="title">Status Motor</div>
        <div class="value">{{ motor }}</div>

        <form method="post" action="/motor">
            <button class="btn btn-on" name="action" value="ON">NYALAKAN</button>
            <button class="btn btn-off" name="action" value="OFF">MATIKAN</button>
        </form>
    </div>

    <footer>
        Auto refresh setiap 3 detik
    </footer>

</div>

<script>
setTimeout(() => location.reload(), 3000);
</script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(
        HTML_PAGE,
        moisture=latest_data["moisture"],
        voltage=latest_data["voltage"],
        motor=latest_data["motor"],
        motor_class="on" if latest_data["motor"] == "ON" else "off"
    )

def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False)

threading.Thread(target=run_flask, daemon=True).start()

# ================== FUNCTION ==================
def moistureValue():
    try:
        raw = chan.value
        voltage = chan.voltage

        value = 100 - (voltage / 3.750) * 100
        value = max(0, min(100, int(value)))

        lcd.lcd_display_string(f"Moisture:{value:3d}% ", 1, 0)
        print(f"RAW: {raw:6d} | Voltage: {voltage:.3f} V | Moisture: {value:3d}%")

        return raw, voltage, value

    except OSError:
        print("? I2C Error")
        lcd.lcd_display_string("ADC ERROR     ", 1, 0)
        return None, None, None

# ================== MAIN LOOP ==================
THRESHOLD = 35

while True:
    raw, voltage, moisture = moistureValue()

    if raw is None:
        sleep(1)
        continue

    latest_data["moisture"] = moisture
    latest_data["voltage"] = round(voltage, 2)

    if moisture < THRESHOLD:
        GPIO.output(relay, GPIO.HIGH)
        lcd.lcd_display_string("Motor   :ON ", 2, 0)
        latest_data["motor"] = "ON"
        motorstatus = False
        sleep(0.5)

    else:
        GPIO.output(relay, GPIO.LOW)
        lcd.lcd_display_string("Motor   :OFF", 2, 0)
        latest_data["motor"] = "OFF"
        motorstatus = True
        sleep(0.5)

    sleep(2)
