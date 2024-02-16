import json

from fastapi import FastAPI, Request
from telegram import Bot
from uvicorn import run

# 初始化 FastAPI 應用和 Telegram Bot
app = FastAPI(docs_url=None, redoc_url=None)
telegram_bot_token = 'YOUR_TELEGRAM_BOT_TOKEN'
telegram_chat_id = 'YOUR_CHAT_ID'
bot = Bot(token=telegram_bot_token)

# 從 JSON 檔案載入 Webhook name 和 key
with open('webhooks.json', 'r') as file:
    webhook_pairs = json.load(file)


# 定義 Webhook 路由
@app.get('/trigger/{webhook_name}/with/key/{webhook_key}')
async def trigger(webhook_name: str, webhook_key: str, value1: str = None, value2: str = None, value3: str = None,
                  request: Request = None):
    # 驗證 Webhook name 和 key
    if webhook_name not in webhook_pairs or webhook_pairs[webhook_name] != webhook_key:
        return {'message': 'Errors! You sent an invalid key'}

    message_components = []

    # 檢查是否存在 JSON 數據
    if request.headers.get('content-type') == 'application/json':
        try:
            json_data = await request.json()
        except json.JSONDecodeError:
            json_data = {}
    else:
        json_data = {}

    # 根據 value 值和 JSON 數據的存在來建立訊息
    if value1:
        message_components.append(value1)
    if value2:
        message_components.append(value2)
    if value3:
        message_components.append(value3)
    if json_data:
        message_components.append(json.dumps(json_data))

    # 檢查是否有數據需要發送
    if message_components:
        message = '\n'.join(message_components)
        await bot.send_message(chat_id=telegram_chat_id, text=message)
        return {'message': f'Congratulations! You\'ve fired the {webhook_name} event', 'data': message}
    else:
        return {'message': 'Errors! No data to send'}


if __name__ == '__main__':
    run(app, host='127.0.0.1', port=8000, server_header=False)
