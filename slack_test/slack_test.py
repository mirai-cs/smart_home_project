import os
from slack_bolt import App
from dotenv import load_dotenv
from slack_bolt.adapter.socket_mode import SocketModeHandler
import subprocess
import time
import logging

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s", 
    handlers=[
        logging.FileHandler("smart_home.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 環境変数から読み込む
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
    "all off": ["light:warm","light:dark","light:dark","aircon:off"]
}

def send_ir_command(labels):
    logger.info(f"送信開始: {labels}")
    GPIO_PIN = "21"
    DATA_FILE = "signals.json"
    SCRIPT_PATH = "irrp.py"

    if not os.path.exists(SCRIPT_PATH):
        return False
    try:
        for label in labels:
            logger.debug(f"送信中: {label}")
            subprocess.run(
                ["python3", SCRIPT_PATH, "-p", "-g", GPIO_PIN, "-f", DATA_FILE, label],
                check=True,            
                capture_output=True,   
                text=True             
            )
            time.sleep(0.5)
        return True
    except Exception as e:
        logger.error(f"送信エラー: {e}", exc_info=True)
        return False


@app.event("message")
def handle_message_events(body, logger, say):
    event = body.get("event", {})
    text = event.get("text", "").strip().lower() # 前後の空白を削除
    if text in COMMAND_MAP:
        labels = COMMAND_MAP[text]
        say(f"コマンド : {text}を実行します...")
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
