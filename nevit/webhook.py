from flask import Flask, request
import json
import asyncio

class WebhookServer:
    def __init__(self, bot, host: str = "0.0.0.0", port: int = 8443):
        self.bot = bot
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/webhook', methods=['POST'])
        def webhook():
            update = request.json
            asyncio.run(self.bot._process_update(update))
            return 'ok'
    
    def run(self):
        self.app.run(host=self.host, port=self.port)
    
    def set_webhook(self, url: str):
        return self.bot.client.set_webhook(url)
    
    def delete_webhook(self):
        return self.bot.client.delete_webhook()