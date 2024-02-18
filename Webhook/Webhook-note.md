# Deploy Webhook to Server

## Overview

This is a guide on how to deploy a webhook to a server from scratch.

This process covers how to set up and use a Python script based on FastAPI and python-telegram-bot, and how to configure the server environment to automatically start and maintain the Webhook service.

In addition, we will also explore how to use MyDNS.JP to register a free second-level domain name, configure a reverse proxy, and ensure communication security by obtaining a TLS certificate.

## Python Script

The script uses [FastAPI](https://github.com/tiangolo/fastapi) and [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot):

	import json
	import logging

	from fastapi import FastAPI, Request, HTTPException
	from telegram import Bot
	from uvicorn import run

	# 開啓日志
	LOG_ENABLED = True

	# 初始化 FastAPI 和 Telegram Bot
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

Contact [@BotFather](https://t.me/BotFather) to obtain the `telegram_bot_token`.

Contact [@IDBot](https://telegram.me/myidbot) to get the `telegram_chat_id`.

Reference: [Telegram event handler](https://docs.influxdata.com/kapacitor/v1/reference/event_handlers/telegram)

Don't forget to create a json file that holds the webhook names and webhook keys:

    {
        "Webhook name 1": "Webhook key 1",
        "Webhook name 2": "Webhook key 2"
    }

Push files to the server and put them in `/usr/local/bin/webhook`.

Install these packages on the server:

	pip install fastapi uvicorn python-telegram-bot python-json-logger

## Systemd

Set up a systemd service for automatically starting the webhook service at server boot.

### Create Service File

Create a new systemd service file:

    sudo vim /etc/systemd/system/webhook.service

In the editor that opens, paste the following:

    [Unit]
    Description=Webhook Service
    After=network.target
    
    [Service]
    User=root
    Group=root
    WorkingDirectory=/usr/local/bin/webhook
    ExecStart=/usr/bin/env uvicorn main:app
    Restart=always
    
    [Install]
    WantedBy=multi-user.target

### Enable and Starting Service

After saving and closing the service file, reload the systemd configuration to enable and start the webhook service:

    sudo systemctl daemon-reload
    sudo systemctl enable webhook.service
    sudo systemctl start webhook.service

### Check Service Status

Confirm that the service is running:

    sudo systemctl status webhook.service

From the output it should contain `Active: active (running)` and `Uvicorn running on http://0.0.0.0:8000`.

## MyDNS.JP

Choose a free second-level domain at [MyDNS.JP](https://www.mydns.jp/join-us).

After registering with MyDNS.JP, please check your masterID and password in the e-mail address you provided during registration.

**Note that email may be judged as spam.**

### Choose Domain

Please choose Free Sub Domain of MyDNS.JP in [`DOMAIN INFO`](https://www.mydns.jp/members/#domaininfo) -> `Input Required` -> `Domain`.

Free Sub-Domain List:
- ???.mydns.jp
- ???.mydns.bz
- ???.mydns.vc
- ???.mydns.tw
- ???.0am.jp
- ???.0g0.jp
- ???.0j0.jp
- ???.0t0.jp
- ???.pgw.jp
- ???.wjg.jp
- ???.dix.asia
- ???.daemon.asia
- ???.live-on.net
- ???.keyword-on.net
- ???.server-on.net

ex: webhook.mydns.jp, chiba.daemon.asia, do.live-on.net, etc ...

Reference: [How to Use](https://www.mydns.jp/#howtouse)

## Crontab

Send IP to MyDNS.JP every 10 minutes on the server.

Edit the current user's crontab:

    crontab -e

If this is your first time using crontab, you may be prompted to choose an editor, such as vim or nano.

Add a crontab task:

    */10 * * * * curl -u masterID:password https://www.mydns.jp/login.html

Please replace `masterID` and `password` with the ones provided in the email.

Look at the list of crontab tasks and make sure the task has been added:

    crontab -l

The webhook can be triggered by visiting:

    http://yourdomain.mydns.jp:8000/trigger/webhook_name/with/key/webhook_key?value1=Hello

## Reverse Proxy

Configuring a reverse proxy on the server avoids using the port directly.

### Configure Nginx

Add a new server block to the Nginx configuration file `grpc.conf` to listen on port 80:

    server {
    	listen 80;
    	server_name yourdomain.mydns.jp;
    
    	location /trigger {
    		proxy_pass http://localhost:8000/trigger;
    		proxy_http_version 1.1;
    		proxy_set_header Host $host;
    		proxy_set_header X-Real-IP $remote_addr;
    		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    		proxy_set_header X-Forwarded-Proto $scheme;
    	}
    	
    	root /path/to/your/root;
    	index index.html;
    }

Please replace `yourdomain.mydns.jp` and `/path/to/your/root` with your domain name and website root.

Please place the `index.html` file to `/path/to/your/root`:

    <!DOCTYPE html>
    
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hello World</title>
    </head>
    <body>
        <h1>Welcome!</h1>
        <p>This is a simple HTML page.</p>
    </body>
    </html>

The webhook can be triggered by visiting:

    http://yourdomain.mydns.jp/trigger/webhook_name/with/key/webhook_key?value1=Hello

## HTTPS

Apply for a TLS certificate for a domain name to enable encrypted link transmission.

### acme.sh

Install [acme.sh](https://github.com/acmesh-official/acme.sh) on server:

    curl https://get.acme.sh | sh    
    source ~/.bashrc

### ZeroSSL

Register for a [ZeroSSL](https://zerossl.com) account:

    acme.sh --register-account -m youremail@example.com --server zerossl

Please replace `youremail@example.com` with your Email address.

### Certificate Request

Obtain a certificate for `yourdomain.mydns.jp`:

    acme.sh --issue -d yourdomain.mydns.jp --webroot /path/to/your/root --server zerossl

Don't forget `/path/to/your/root` is website root.

This is where acwme.sh verifies your control of the domain (via HTTP verification).

### Install Certificate

Install the certificate on the server:

    acme.sh --install-cert -d yourdomain.mydns.jp \
    --cert-file /path/to/your/nginx/cert.pem \
    --key-file /path/to/your/nginx/key.pem \
    --fullchain-file /path/to/your/nginx/fullchain.pem \
    --reloadcmd "sudo nginx -s reload"

Please replace `/path/to/your/nginx` with the actual path where your Nginx certificate is stored.

### Update Nginx Configuration

Add a new server block, reference the new certificate and private key file paths:

    server {
        	listen 443 ssl http2;
        	server_name yourdomain.mydns.jp;
    
        	ssl_certificate /path/to/your/nginx/fullchain.pem;
        	ssl_certificate_key /path/to/your/nginx/key.pem;
        	ssl_session_timeout 1d;
        	ssl_protocols TLSv1.2 TLSv1.3;
        	ssl_ciphers HIGH:!aNULL:!MD5;
        	ssl_prefer_server_ciphers on;
    
        	location /trigger {
            	proxy_pass http://localhost:8000/trigger;
            	proxy_http_version 1.1;
            	proxy_set_header Host $host;
            	proxy_set_header X-Real-IP $remote_addr;
            	proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            	proxy_set_header X-Forwarded-Proto $scheme;
        	}
    
        	root /path/to/your/root;
            index index.html;
    }

Please replace `/path/to/your/nginx/fullchain.pem` and `/path/to/your/nginx/key.pem` with the corresponding files in the `/path/to/your/nginx` folder.

Restart Nginx:

    sudo nginx -s reload

The webhook can be triggered by visiting:

    https://yourdomain.mydns.jp/trigger/webhook_name/with/key/webhook_key?value1=Hello

The webhook deployment is completed. :)

## Follow Up

If you change the Python script, please restart the systemd service:

    sudo systemctl restart webhook.service

If you need to change the domain name:

1. On the MyDNS.JP, visit the [Domain INFO](https://www.mydns.jp/members/#domaininfo) section and change to the new domain name.

2. In the `grpc.conf` file, find the `server_name` directive and update it with the new domain name.

3. Update the server's IP address. This can be done by updating manually in [IP Address Direct](https://www.mydns.jp/members/#ipinfo) in MyDNS.JP, or automatically by executing the curl command on the server.

4. Restart the Nginx service:

	   sudo nginx -s reload

Link to this article: [Webhook-note](https://github.com/finn-chan/notes/blob/main/Webhook/Webhook-note.md)
