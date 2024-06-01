import json
import logging

from fastapi import FastAPI, Request, HTTPException
from telegram import Bot
from uvicorn import run

# Enable logging
LOG_ENABLED = True

# Initialize FastAPI application
app = FastAPI(docs_url=None, redoc_url=None)

# Load webhook configuration from JSON file
try:
    with open('webhooks.json', 'r') as file:
        webhook_config = json.load(file)
except Exception as e:
    logging.error(f'Failed to load webhooks.json: {e}.')
    raise e

# Set up the log file
if LOG_ENABLED:
    log_file_path = 'webhook_service.log'
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_file_path, mode='a')
                            # logging.StreamHandler()
                        ])

# Define webhook route
@app.get('/trigger/{webhook_name}/with/key/{webhook_key}')
async def trigger(webhook_name: str, webhook_key: str, value1: str = None, value2: str = None, value3: str = None,
                  request: Request = None):
    try:
        # Validate webhook name and key
        for webhook in webhook_config["webhooks"]:
            if webhook["name"] == webhook_name:
                for mapping in webhook["mappings"]:
                    if mapping["key"] == webhook_key:
                        bot = Bot(token=mapping["telegram"]["bot_token"])
                        chat_id = mapping["telegram"]["chat_id"]
                        break
                else:
                    continue

                break
        else:
            return {'message': 'Error: Invalid webhook name or key.'}

        message_components = []

        # Construct the message based on the value fields and JSON data presence
        if value1:
            message_components.append(value1)
        if value2:
            message_components.append(value2)

        # Check for JSON data presence
        if request.headers.get('content-type') == 'application/json':
            try:
                json_data = await request.json()
            except json.JSONDecodeError:
                logging.error('JSON decoding failed.')
                json_data = {}
            if json_data:
                message_components.append(json.dumps(json_data, ensure_ascii=False))

        # Check if there is data to send
        if message_components:
            message = '\n'.join(message_components)
            parse_mode = None

            # Choose parse mode based on value3
            if value3 == 'MarkdownV2':
                parse_mode = 'MarkdownV2'
            elif value3 == 'HTML':
                parse_mode = 'HTML'
            elif value3 == 'Markdown':
                parse_mode = 'Markdown'

            # Send the message
            await bot.send_message(chat_id=chat_id, text=message, parse_mode=parse_mode)
            logging.info(f'Message sent successfully:\n{message}.')
            return {'message': f'Congratulations! You\'ve fired the {webhook_name} event.', 'data': message}
        else:
            logging.warning('No data to send.')
            return {'message': 'Error: No data to send.'}

    except Exception as e:
        logging.error(f'An error occurred: {e}.', exc_info=True)
        raise HTTPException(status_code=500, detail='Internal Server Error.')


if __name__ == '__main__':
    run(app, host='127.0.0.1', port=8000, server_header=False)