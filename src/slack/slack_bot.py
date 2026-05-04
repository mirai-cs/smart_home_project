import os
import sys
from slack_bolt import App
from dotenv import load_dotenv
from slack_bolt.adapter.socket_mode import SocketModeHandler
import subprocess
import time
import logging
import board
import busio
import adafruit_bme680

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s", 
    handlers=[
        logging.FileHandler("smarthome.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

try:
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x76)
    sensor.sea_level_pressure = 1013.25
    logger.info("BME680 initialization successful")
except Exception as e:
    sensor = None
    logger.error("BME680 Initialization failure", exc_info=True)

load_dotenv()
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")    # xoxb-...
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")    # xapp-...
app = App(token=SLACK_BOT_TOKEN)
COMMAND_MAP = {
    "light on": ["light:on"],
    "light dark": ["light:dark"],
    "light warm": ["light:warm"],
    "light off" : ["light:warm","light:dark","light:dark"],
    "aircon heater": ["aircon:on:heater"],
    "aircon cooler": ["aircon:on:cooler"],
    "aircon dry": ["aircon:on:dry"],
    "aircon off": ["aircon:off"],
    "all off": ["light:warm","light:dark","light:dark","aircon:off"],
    "light alarm" :["light:on","light:dark","light:on","light:dark","light:on"],
    "test" :["light:on","light:on","light:on","light:on","aircon:off","aircon:off","aircon:off","aircon:off"]
}

def get_status_text():
    if sensor is None:
        return "センサが接続されていません。"

    try:
        temp = sensor.temperature
        hum = sensor.humidity
        pres = sensor.pressure
        gas = sensor.gas

        return (
            f"現在の環境:\n"
            f"温度: {temp:.2f} ℃\n"
            f"湿度: {hum:.2f} %\n"
            f"気圧: {pres:.2f} hPa\n"
            f"ガス抵抗: {gas} Ω"
        )
    except Exception as e:
        logger.error("Sensor read failure ", exc_info=True)
        return "センサ計測に失敗しました。"


def send_ir_command(labels):
    logger.info(f"send: {labels}")
    GPIO_PIN = "21"
    DATA_FILE = "signals.json"
    SCRIPT_PATH = "irrp.py"

    if not os.path.exists(SCRIPT_PATH):
        return False
    try:
        for label in labels:
            logger.debug(f"sending: {label}")
            subprocess.run(
                [sys.executable, SCRIPT_PATH, "-p", "-g", GPIO_PIN, "-f", DATA_FILE, label],
                check=True,            
                capture_output=True,   
                text=True             
            )
            time.sleep(0.5)
        return True
    except Exception as e:
        logger.error(f"error: {e}", exc_info=True)
        return False


@app.event("message")
def handle_message_events(body, logger, say):
    event = body.get("event", {})
    text = event.get("text", "").strip().lower() 
    if text == "status":
        say("センサ計測中です...")
        status = get_status_text()
        say(status)
        return
        
    if text in COMMAND_MAP:
        labels = COMMAND_MAP[text]
        say(f"コマンド : {text}を実行しています...")
        success = send_ir_command(labels)
        if success:
            say("信号の送信が完了しました。")
        else:
            say("信号の送信に失敗しました。ログを確認してください。")
    else:
        say(f"無効なコマンドです： {text}")
    
if __name__ == "__main__":
    handler = SocketModeHandler(
        app,
        SLACK_APP_TOKEN
    )
    handler.start()
