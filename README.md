NEVIT Library

A modern, powerful and easy-to-use Python library for building bots on Bale messenger


✨ Features

🚀 Simple & Intuitive - Clean, Pythonic API design
📨 Full Message Support - Text, photos, videos, documents and more
⌨️ Interactive Elements - Inline keyboards, reply keyboards and buttons
🔄 Real-time Updates - Webhook and polling support
📁 File Handling - Easy upload and download of media files
🛡️ Error Handling - Comprehensive exception handling
📖 Type Hints - Full typing support for better development experience
⚡ Async/Sync Support - Both synchronous and asynchronous programming


📦 Installation

pip install nevit

Or from PyPI main:

pip install --index-url https://pypi.org/simple nevit


🚀 Quick Start

from nevit import NevitBot

bot = NevitBot("YOUR_BOT_TOKEN")

@bot.command(["start"])
def start(message):
    bot.reply(message, "Hello! Welcome to NEVIT Bot")

bot.run()


📚 Examples


1. Echo Bot

from nevit import NevitBot, Filters

bot = NevitBot("YOUR_BOT_TOKEN")

@bot.message(Filters.text)
def echo(message):
    bot.reply(message, message.text)

bot.run()


2. Inline Keyboard

from nevit import NevitBot

bot = NevitBot("YOUR_BOT_TOKEN")

@bot.command(["start"])
def start(message):
    bot.reply(message, "Choose an option:", reply_markup=bot.keyboard([
        ["🔗 Link", "https://google.com"],
        ["📚 Docs", "docs"],
        ["📥 Install", "install"]
    ]))

@bot.callback("docs")
def docs(callback, data):
    bot.edit_message_text(callback.chat.id, callback.message_id, "Documentation: pypi.org/project/nevit")
    bot.answer_callback(callback.id)

bot.run()


3. Conversation Bot

from nevit import NevitBot

bot = NevitBot("YOUR_BOT_TOKEN")

@bot.command(["start"])
def start(message):
    bot.set_state(message.from_user.id, "waiting_for_name")
    bot.reply(message, "Hi! What's your name?")

@bot.message()
def handle_name(message):
    if bot.get_state(message.from_user.id) == "waiting_for_name":
        name = message.text
        bot.clear_state(message.from_user.id)
        bot.reply(message, f"Welcome {name}!")

bot.run()


4. Filters Example

from nevit import NevitBot, Filters

bot = NevitBot("YOUR_BOT_TOKEN")

@bot.message(Filters.text)
def handle_text(message):
    bot.reply(message, f"📩 Your text: {message.text}")

@bot.message(Filters.photo)
def handle_photo(message):
    bot.reply(message, "📸 Photo received!")

@bot.message(Filters.command)
def handle_command(message):
    bot.reply(message, "⚡ Command received!")

bot.run()


5. Async Bot

from nevit import NevitAsyncBot
import asyncio

bot = NevitAsyncBot("YOUR_BOT_TOKEN")

@bot.command(["start"])
async def start(message):
    await bot.reply(message, "Hello from Async Bot!")

asyncio.run(bot.run())


📖 Core Abilities

✅ Message Handling - Process text, commands and media messages
✅ Callback Queries - Handle inline keyboard interactions
✅ File Operations - Send and receive photos, videos, documents
✅ Chat Management - Get chat info, member management
✅ Custom Keyboards - Create interactive user interfaces
✅ Webhook Support - Production-ready webhook handling
✅ Middleware Support - Add custom processing layers
✅ User State Management - Conversation state handling
✅ Error Handler - Centralized error management


🔧 Available Methods

send_message(chat_id, text) - Send text message
reply(message, text) - Reply to a message
send_photo(chat_id, photo) - Send photo
send_video(chat_id, video) - Send video
send_animation(chat_id, gif) - Send GIF/animation
send_audio(chat_id, audio) - Send audio
send_document(chat_id, document) - Send document
send_sticker(chat_id, sticker) - Send sticker
send_location(chat_id, lat, lon) - Send location
send_contact(chat_id, phone, name) - Send contact
send_poll(chat_id, question, options) - Send poll
delete_message(chat_id, message_id) - Delete message
edit_message_text(chat_id, message_id, text) - Edit message
forward_message(chat_id, from_chat_id, message_id) - Forward message
answer_callback(callback_id, text) - Answer callback query
get_chat(chat_id) - Get chat info
get_chat_member(chat_id, user_id) - Get member info
kick_member(chat_id, user_id) - Kick user
pin_message(chat_id, message_id) - Pin message


🎯 Filters

Filters.text - Text messages
Filters.photo - Photos
Filters.video - Videos
Filters.animation - GIF/Animation
Filters.audio - Audio files
Filters.voice - Voice messages
Filters.document - Documents
Filters.sticker - Stickers
Filters.location - Locations
Filters.contact - Contacts
Filters.command - Commands
Filters.private - Private chats
Filters.group - Groups
Filters.regex(pattern) - Regular expression
Filters.equals(text) - Exact text match
Filters.contains(word) - Contains word
Filters.startswith(prefix) - Starts with
Filters.endswith(suffix) - Ends with
Filters.from_user(user_id) - From specific user


⌨️ Keyboards

bot.keyboard(buttons) - Simple inline keyboard
bot.reply_keyboard(buttons) - Reply keyboard
bot.remove_keyboard() - Remove keyboard


🔄 Decorators

@bot.command(["start", "help"]) - Register command handler
@bot.message(Filters.text) - Register message handler with filter
@bot.callback("data") - Register callback query handler
@bot.on("message") - Event listener for messages
@bot.on("callback") - Event listener for callbacks
@bot.listen(Filters.photo) - Message listener with filter
@bot.error_handler() - Register global error handler


📝 User State Management

bot.set_state(user_id, "state_name", {"key": "value"}) - Set user state
bot.get_state(user_id) - Get current user state
bot.get_state_data(user_id) - Get user state data
bot.clear_state(user_id) - Clear user state

Example:
@bot.command(["form"])
def form(message):
    bot.set_state(message.from_user.id, "waiting_for_name")
    bot.reply(message, "What is your name?")

@bot.message()
def handle_form(message):
    if bot.get_state(message.from_user.id) == "waiting_for_name":
        name = message.text
        bot.clear_state(message.from_user.id)
        bot.reply(message, f"Hello {name}!")


🛠 Middleware

Built-in Middleware:
- LoggingMiddleware - Log all messages
- RateLimitMiddleware - Limit request rate
- AntiSpamMiddleware - Filter spam messages

Usage:
from nevit import LoggingMiddleware, RateLimitMiddleware, AntiSpamMiddleware

bot.add_middleware(LoggingMiddleware(log_text=True, log_user=True))
bot.add_middleware(RateLimitMiddleware(max_requests=5, time_window=60))
bot.add_middleware(AntiSpamMiddleware(blocked_words=["spam", "ad"], max_length=1000))

Custom Middleware:
class MyMiddleware(Middleware):
    async def pre_process(self, message, data):
        print(f"Processing: {message.text}")
        return message
    
    async def post_process(self, message, data, result):
        print("Message processed")


🚨 Error Handler

@bot.error_handler()
def handle_error(error, context):
    print(f"Error: {error}")
    print(f"Context: {context}")
    # Log error to file or database
    with open("error.log", "a") as f:
        f.write(f"{error}\n{context}\n")


⌨️ Keyboard Methods

Simple inline keyboard:
bot.keyboard([
    ["Button 1", "callback_1"],
    ["Button 2", "https://example.com"],
    ["Button 3", "callback_3"]
])

Reply keyboard:
bot.reply_keyboard([
    ["Yes", "No"],
    ["Maybe", "Cancel"]
])

Remove keyboard:
bot.remove_keyboard()


📁 File Handling

Send file from path:
bot.send_photo(chat_id, "path/to/photo.jpg")
bot.send_video(chat_id, "path/to/video.mp4")
bot.send_document(chat_id, "path/to/document.pdf")

Send file from URL:
bot.send_photo(chat_id, "https://example.com/photo.jpg")

Get file info:
file_info = bot.get_file(file_id)
file_url = bot.get_file_url(file_id)


💬 Chat Management

Get chat info:
chat = bot.get_chat(chat_id)

Get administrators:
admins = bot.get_chat_administrators(chat_id)

Get member info:
member = bot.get_chat_member(chat_id, user_id)

Kick user:
bot.kick_member(chat_id, user_id)

Unban user:
bot.unban_member(chat_id, user_id)

Leave chat:
bot.leave_chat(chat_id)

Pin message:
bot.pin_message(chat_id, message_id)


⚡ Async Bot (NevitAsyncBot)

Same methods as NevitBot but async:

from nevit import NevitAsyncBot
import asyncio

bot = NevitAsyncBot("TOKEN")

@bot.command(["start"])
async def start(message):
    await bot.reply(message, "Hello from Async Bot!")

@bot.message(Filters.text)
async def handle_text(message):
    await bot.reply(message, f"Text: {message.text}")

@bot.callback("data")
async def handle_callback(callback, data):
    await bot.answer_callback(callback.id, "Clicked!")

async def main():
    await bot.run()

asyncio.run(main())


📊 Type Hints

All methods support full type hints for better IDE support:

from nevit import NevitBot, Message, User, Chat, Filters
from typing import Optional, List, Dict

def process_message(message: Message) -> Optional[str]:
    if message.text:
        return message.text.upper()
    return None


🔧 Advanced Examples

Admin Bot with Middleware:
from nevit import NevitBot, Filters, LoggingMiddleware, RateLimitMiddleware

bot = NevitBot("TOKEN")
bot.add_middleware(LoggingMiddleware())
bot.add_middleware(RateLimitMiddleware(max_requests=10, time_window=60))

ADMIN_ID = 123456789

@bot.command(["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply(message, "Access denied!")
        return
    bot.reply(message, "Welcome Admin!", reply_markup=bot.keyboard([
        ["📊 Stats", "stats"],
        ["📨 Broadcast", "broadcast"],
        ["👥 Users", "users"]
    ]))

@bot.callback("stats")
def show_stats(callback, data):
    # Show bot statistics
    bot.answer_callback(callback.id, "Total users: 1000")


Support Bot with State:
from nevit import NevitBot

bot = NevitBot("TOKEN")

@bot.command(["support"])
def support(message):
    bot.set_state(message.from_user.id, "support_ticket")
    bot.reply(message, "Please describe your issue:")

@bot.message()
def handle_support(message):
    if bot.get_state(message.from_user.id) == "support_ticket":
        issue = message.text
        bot.clear_state(message.from_user.id)
        # Forward to support team
        bot.forward_message(SUPPORT_CHAT_ID, message.chat.id, message.message_id)
        bot.reply(message, "✅ Your message has been sent to support!")


📋 Complete Method Reference

NevitBot Methods:

Message Sending:
- send_message(chat_id, text, parse_mode=None, reply_to_message_id=None, reply_markup=None)
- reply(message, text, **kwargs)
- send_photo(chat_id, photo, caption=None, reply_markup=None)
- send_video(chat_id, video, caption=None, reply_markup=None)
- send_animation(chat_id, animation, caption=None, reply_markup=None)
- send_audio(chat_id, audio, caption=None, reply_markup=None)
- send_voice(chat_id, voice, caption=None, reply_markup=None)
- send_document(chat_id, document, caption=None, reply_markup=None)
- send_sticker(chat_id, sticker, reply_markup=None)
- send_location(chat_id, latitude, longitude, reply_markup=None)
- send_contact(chat_id, phone_number, first_name, last_name=None, reply_markup=None)
- send_poll(chat_id, question, options, is_anonymous=True, reply_markup=None)
- send_dice(chat_id, emoji=None, reply_markup=None)
- send_media_group(chat_id, media)
- send_chat_action(chat_id, action)

Message Management:
- delete_message(chat_id, message_id)
- edit_message_text(chat_id, message_id, text, reply_markup=None)
- forward_message(chat_id, from_chat_id, message_id)
- copy_message(chat_id, from_chat_id, message_id, caption=None, reply_markup=None)
- answer_callback(callback_id, text=None, show_alert=False)

Chat Management:
- get_chat(chat_id)
- get_chat_administrators(chat_id)
- get_chat_member(chat_id, user_id)
- get_chat_members_count(chat_id)
- kick_member(chat_id, user_id)
- unban_member(chat_id, user_id)
- leave_chat(chat_id)
- pin_message(chat_id, message_id, disable_notification=None)
- unpin_message(chat_id, message_id=None)

User State:
- set_state(user_id, state, data=None)
- get_state(user_id)
- get_state_data(user_id)
- clear_state(user_id)

Keyboard:
- keyboard(buttons)
- reply_keyboard(buttons, resize=True)
- remove_keyboard()

Middleware:
- add_middleware(middleware)

Decorators:
- command(commands)
- message(filters)
- callback(pattern)
- on(event)
- listen(filters)
- error_handler()


💡 Tips

1. Always use environment variables for tokens
2. Enable logging for debugging
3. Use webhook in production instead of polling
4. Implement rate limiting for public bots
5. Handle exceptions properly
6. Use async version for high-load bots
7. Keep bot token secret
8. Test with small user group first


🐛 Debugging

Enable debug logging:
import logging
logging.basicConfig(level=logging.DEBUG)

Check bot info:
print(bot.bot_info)

Test API connection:
me = bot.client.get_me()
print(me)


📞 Support & Community

- 📖 Documentation: https://pypi.org/project/nevit
- 🐛 Issue Tracker: https://github.com/amir3478mm-coder/nevit/issues
- 💬 Telegram: @nevit_support
- 📧 Email: support@nevit.ir


🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (git checkout -b feature/AmazingFeature)
3. Commit your changes (git commit -m 'Add some AmazingFeature')
4. Push to the branch (git push origin feature/AmazingFeature)
5. Open a Pull Request


📄 License

MIT License - Free for everyone

Copyright (c) 2026 NEVIT Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


⭐ Show Your Support

If you like NEVIT Library, please give it a star on GitHub!
