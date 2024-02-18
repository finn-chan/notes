import json
import logging

from fastapi import FastAPI, Request, HTTPException
from telegram import Bot
from uvicorn import run

# 開啓日志
LOG_ENABLED = True

# 初始化 FastAPI 應用和 Telegram Bot
app = FastAPI(docs_url=None, redoc_url=None)
telegram_bot_token = 'YOUR_TELEGRAM_BOT_TOKEN'
telegram_chat_id = 'YOUR_CHAT_ID'
bot = Bot(token=telegram_bot_token)

# 從 JSON 檔案載入 Webhook name 和 key
try:
    with open('webhooks.json', 'r') as file:
        webhook_pairs = json.load(file)
except Exception as e:
    logging.error(f'Failed to load webhooks.json: {e}')
    raise e

# 將日志保存到文檔中
if LOG_ENABLED:
    log_file_path = 'webhook_service.log'
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_file_path, mode='a')
                            # logging.StreamHandler()
                        ])


# 定義 Webhook 路由
@app.get('/trigger/{webhook_name}/with/key/{webhook_key}')
async def trigger(webhook_name: str, webhook_key: str, value1: str = None, value2: str = None, value3: str = None,
                  request: Request = None):
    try:
        # 驗證 Webhook name 和 key
        if webhook_name not in webhook_pairs or webhook_pairs[webhook_name] != webhook_key:
            return {'message': 'Errors! You sent an invalid key'}

        message_components = []

        # 根據 value 值和 JSON 數據的存在來建立訊息
        if value1:
            message_components.append(value1)
        if value2:
            message_components.append(value2)

        # 檢查是否存在 JSON 數據
        if request.headers.get('content-type') == 'application/json':
            try:
                json_data = await request.json()
            except json.JSONDecodeError:
                logging.error('JSON decoding failed')
                json_data = {}
            if json_data:
                message_components.append(json.dumps(json_data, ensure_ascii=False))

        # 檢查是否有數據需要發送
        if message_components:
            message = '\n'.join(message_components)
            parse_mode = None

            # 根據 value3 的值選擇解析模式
            if value3 == 'MarkdownV2':
                parse_mode = 'MarkdownV2'
            elif value3 == 'HTML':
                parse_mode = 'HTML'
            elif value3 == 'Markdown':
                parse_mode = 'Markdown'

            # 發送訊息
            await bot.send_message(chat_id=telegram_chat_id, text=message, parse_mode=parse_mode)
            logging.info(f'Message sent successfully:\n{message}')
            return {'message': f'Congratulations! You\'ve fired the {webhook_name} event', 'data': message}
        else:
            logging.warning('No data to send')
            return {'message': 'Error: No data to send'}

    except Exception as e:
        logging.error(f'An error occurred: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Internal Server Error')


if __name__ == '__main__':
    run(app, host='127.0.0.1', port=8000, server_header=False)
