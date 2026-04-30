import time
import board
import busio
import adafruit_bme680

# I2C初期化
i2c = busio.I2C(board.SCL, board.SDA)

# アドレスは環境に応じて変更（0x76 or 0x77）
sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x76)

# 任意設定（海面気圧）
sensor.sea_level_pressure = 1013.25

while True:
    print("Temperature: %.2f C" % sensor.temperature)
    print("Humidity: %.2f %%" % sensor.humidity)
    print("Pressure: %.2f hPa" % sensor.pressure)
    print("Gas: %d ohm" % sensor.gas)
    print("----------------------")
    time.sleep(2)
