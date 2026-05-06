import httpx
import asyncio
import json
import logging
import os
import requests
from typing import Optional, List, Dict, Any

logger = logging.getLogger("nevit")

class NevitClient:
    def __init__(self, token: str, request_timeout: int = 30):
        self.token = token
        self.base_url = f"https://tapi.bale.ai/bot{token}"
        self.request_timeout = request_timeout
        self._session = requests.Session()
        self._client = httpx.Client(timeout=request_timeout)
    
    def _request(self, method: str, data: dict = None, files: dict = None) -> dict:
        url = f"{self.base_url}/{method}"
        try:
            if files:
                response = self._client.post(url, data=data, files=files)
            else:
                response = self._client.post(url, json=data)
            return response.json()
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"ok": False, "error": str(e)}
    
    def _request_sync(self, method: str, data: dict = None, files: dict = None) -> dict:
        url = f"{self.base_url}/{method}"
        try:
            if files:
                response = self._session.post(url, data=data, files=files, timeout=self.request_timeout)
            else:
                response = self._session.post(url, json=data, timeout=self.request_timeout)
            return response.json()
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"ok": False, "error": str(e)}
    
    def _send_file(self, method: str, data: dict, file_key: str, file_value: str) -> dict:
        url = f"{self.base_url}/{method}"
        try:
            if os.path.isfile(file_value):
                files = {file_key: open(file_value, 'rb')}
            else:
                files = {file_key: file_value}
            response = self._session.post(url, data=data, files=files, timeout=self.request_timeout)
            return response.json()
        except Exception as e:
            logger.error(f"File upload error: {e}")
            return {"ok": False, "error": str(e)}
    
    def get_me(self) -> dict:
        return self._request("getMe")
    
    def get_updates(self, offset: int = None, limit: int = 100, timeout: int = 60) -> dict:
        data = {"timeout": timeout, "limit": limit}
        if offset is not None:
            data["offset"] = offset
        return self._request("getUpdates", data)
    
    def get_webhook_info(self) -> dict:
        return self._request("getWebhookInfo")
    
    def set_webhook(self, url: str, max_connections: int = 40,
                    allowed_updates: List[str] = None) -> dict:
        data = {"url": url, "max_connections": max_connections}
        if allowed_updates:
            data["allowed_updates"] = allowed_updates
        return self._request("setWebhook", data)
    
    def delete_webhook(self) -> dict:
        return self._request("deleteWebhook")
    
    def approve_chat_join_request(self, chat_id: int, user_id: int) -> dict:
        return self._request("approveChatJoinRequest", {"chat_id": chat_id, "user_id": user_id})
    
    def decline_chat_join_request(self, chat_id: int, user_id: int) -> dict:
        return self._request("declineChatJoinRequest", {"chat_id": chat_id, "user_id": user_id})
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = None,
                     disable_web_page_preview: bool = None,
                     disable_notification: bool = None,
                     reply_to_message_id: int = None,
                     reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "text": text}
        if parse_mode: data["parse_mode"] = parse_mode
        if disable_web_page_preview: data["disable_web_page_preview"] = disable_web_page_preview
        if disable_notification: data["disable_notification"] = disable_notification
        if reply_to_message_id: data["reply_to_message_id"] = reply_to_message_id
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendMessage", data)
    
    def send_photo(self, chat_id: int, photo: str, caption: str = None,
                   parse_mode: str = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(photo):
            return self._send_file("sendPhoto", data, "photo", photo)
        data["photo"] = photo
        if caption: data["caption"] = caption
        if parse_mode: data["parse_mode"] = parse_mode
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendPhoto", data)
    
    def send_audio(self, chat_id: int, audio: str, caption: str = None,
                   duration: int = None, performer: str = None, title: str = None,
                   reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(audio):
            return self._send_file("sendAudio", data, "audio", audio)
        data["audio"] = audio
        if caption: data["caption"] = caption
        if duration: data["duration"] = duration
        if performer: data["performer"] = performer
        if title: data["title"] = title
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendAudio", data)
    
    def send_voice(self, chat_id: int, voice: str, caption: str = None,
                   duration: int = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(voice):
            return self._send_file("sendVoice", data, "voice", voice)
        data["voice"] = voice
        if caption: data["caption"] = caption
        if duration: data["duration"] = duration
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendVoice", data)
    
    def send_video(self, chat_id: int, video: str, caption: str = None,
                   duration: int = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(video):
            return self._send_file("sendVideo", data, "video", video)
        data["video"] = video
        if caption: data["caption"] = caption
        if duration: data["duration"] = duration
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendVideo", data)
    
    def send_animation(self, chat_id: int, animation: str, caption: str = None,
                       duration: int = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(animation):
            return self._send_file("sendAnimation", data, "animation", animation)
        data["animation"] = animation
        if caption: data["caption"] = caption
        if duration: data["duration"] = duration
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendAnimation", data)
    
    def send_document(self, chat_id: int, document: str, caption: str = None,
                     reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(document):
            return self._send_file("sendDocument", data, "document", document)
        data["document"] = document
        if caption: data["caption"] = caption
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendDocument", data)
    
    def send_sticker(self, chat_id: int, sticker: str, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(sticker):
            return self._send_file("sendSticker", data, "sticker", sticker)
        data["sticker"] = sticker
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendSticker", data)
    
    def send_location(self, chat_id: int, latitude: float, longitude: float,
                      live_period: int = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "latitude": latitude, "longitude": longitude}
        if live_period: data["live_period"] = live_period
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendLocation", data)
    
    def send_venue(self, chat_id: int, latitude: float, longitude: float,
                  title: str, address: str, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "latitude": latitude, "longitude": longitude,
                "title": title, "address": address}
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendVenue", data)
    
    def send_contact(self, chat_id: int, phone_number: str, first_name: str,
                    last_name: str = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "phone_number": phone_number, "first_name": first_name}
        if last_name: data["last_name"] = last_name
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendContact", data)
    
    def send_poll(self, chat_id: int, question: str, options: List[str],
                 is_anonymous: bool = True, type: str = "regular",
                 allows_multiple_answers: bool = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "question": question, "options": options,
                "is_anonymous": is_anonymous, "type": type}
        if allows_multiple_answers is not None:
            data["allows_multiple_answers"] = allows_multiple_answers
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendPoll", data)
    
    def send_dice(self, chat_id: int, emoji: str = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if emoji: data["emoji"] = emoji
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendDice", data)
    
    def send_game(self, chat_id: int, game_short_name: str, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "game_short_name": game_short_name}
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendGame", data)
    
    def send_media_group(self, chat_id: int, media: List[dict]) -> dict:
        return self._request("sendMediaGroup", {"chat_id": chat_id, "media": json.dumps(media)})
    
    def send_chat_action(self, chat_id: int, action: str) -> dict:
        return self._request("sendChatAction", {"chat_id": chat_id, "action": action})
    
    def forward_message(self, chat_id: int, from_chat_id: int, message_id: int) -> dict:
        return self._request("forwardMessage", {
            "chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id
        })
    
    def copy_message(self, chat_id: int, from_chat_id: int, message_id: int,
                    caption: str = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id}
        if caption: data["caption"] = caption
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("copyMessage", data)
    
    def delete_message(self, chat_id: int, message_id: int) -> dict:
        return self._request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    
    def edit_message_text(self, chat_id: int, message_id: int, text: str,
                         parse_mode: str = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if parse_mode: data["parse_mode"] = parse_mode
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("editMessageText", data)
    
    def edit_message_reply_markup(self, chat_id: int, message_id: int, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "message_id": message_id}
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("editMessageReplyMarkup", data)
    
    def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False) -> dict:
        data = {"callback_query_id": callback_query_id}
        if text:
            data["text"] = text
        if show_alert:
            data["show_alert"] = show_alert
        return self._request("answerCallbackQuery", data)
    
    def get_chat(self, chat_id: int) -> dict:
        return self._request("getChat", {"chat_id": chat_id})
    
    def get_chat_administrators(self, chat_id: int) -> dict:
        return self._request("getChatAdministrators", {"chat_id": chat_id})
    
    def get_chat_member(self, chat_id: int, user_id: int) -> dict:
        return self._request("getChatMember", {"chat_id": chat_id, "user_id": user_id})
    
    def get_chat_members_count(self, chat_id: int) -> dict:
        return self._request("getChatMembersCount", {"chat_id": chat_id})
    
    def kick_chat_member(self, chat_id: int, user_id: int) -> dict:
        return self._request("kickChatMember", {"chat_id": chat_id, "user_id": user_id})
    
    def unban_chat_member(self, chat_id: int, user_id: int) -> dict:
        return self._request("unbanChatMember", {"chat_id": chat_id, "user_id": user_id})
    
    def restrict_chat_member(self, chat_id: int, user_id: int, permissions: dict) -> dict:
        return self._request("restrictChatMember", {
            "chat_id": chat_id, "user_id": user_id, "permissions": permissions
        })
    
    def promote_chat_member(self, chat_id: int, user_id: int, **kwargs) -> dict:
        data = {"chat_id": chat_id, "user_id": user_id}
        data.update(kwargs)
        return self._request("promoteChatMember", data)
    
    def set_chat_title(self, chat_id: int, title: str) -> dict:
        return self._request("setChatTitle", {"chat_id": chat_id, "title": title})
    
    def set_chat_description(self, chat_id: int, description: str) -> dict:
        return self._request("setChatDescription", {"chat_id": chat_id, "description": description})
    
    def set_chat_photo(self, chat_id: int, photo: str) -> dict:
        return self._send_file("setChatPhoto", {"chat_id": chat_id}, "photo", photo)
    
    def delete_chat_photo(self, chat_id: int) -> dict:
        return self._request("deleteChatPhoto", {"chat_id": chat_id})
    
    def export_chat_invite_link(self, chat_id: int) -> dict:
        return self._request("exportChatInviteLink", {"chat_id": chat_id})
    
    def create_chat_invite_link(self, chat_id: int, expire_date: int = None,
                                 member_limit: int = None) -> dict:
        data = {"chat_id": chat_id}
        if expire_date: data["expire_date"] = expire_date
        if member_limit: data["member_limit"] = member_limit
        return self._request("createChatInviteLink", data)
    
    def leave_chat(self, chat_id: int) -> dict:
        return self._request("leaveChat", {"chat_id": chat_id})
    
    def pin_chat_message(self, chat_id: int, message_id: int,
                        disable_notification: bool = None) -> dict:
        data = {"chat_id": chat_id, "message_id": message_id}
        if disable_notification: data["disable_notification"] = disable_notification
        return self._request("pinChatMessage", data)
    
    def unpin_chat_message(self, chat_id: int, message_id: int = None) -> dict:
        data = {"chat_id": chat_id}
        if message_id: data["message_id"] = message_id
        return self._request("unpinChatMessage", data)
    
    def get_file(self, file_id: str) -> dict:
        return self._request("getFile", {"file_id": file_id})
    
    def get_file_url(self, file_id: str) -> Optional[str]:
        result = self.get_file(file_id)
        if result.get("ok"):
            file_path = result["result"]["file_path"]
            return f"https://tapi.bale.ai/file/bot{self.token}/{file_path}"
        return None
    
    def download_file(self, file_id: str, destination: str = None) -> Optional[bytes]:
        url = self.get_file_url(file_id)
        if url:
            response = self._session.get(url)
            if destination:
                with open(destination, 'wb') as f:
                    f.write(response.content)
            return response.content
        return None
    
    def set_my_commands(self, commands: List[dict]) -> dict:
        return self._request("setMyCommands", {"commands": commands})
    
    def get_my_commands(self) -> dict:
        return self._request("getMyCommands")
    
    def delete_my_commands(self) -> dict:
        return self._request("deleteMyCommands")
    
    def answer_inline_query(self, inline_query_id: str, results: List[dict],
                           cache_time: int = 300, next_offset: str = None) -> dict:
        data = {"inline_query_id": inline_query_id, "results": results, "cache_time": cache_time}
        if next_offset: data["next_offset"] = next_offset
        return self._request("answerInlineQuery", data)
    
    def send_invoice(self, chat_id: int, title: str, description: str,
                    payload: str, provider_token: str, currency: str,
                    prices: List[dict], reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "title": title, "description": description,
                "payload": payload, "provider_token": provider_token, "currency": currency,
                "prices": prices}
        if reply_markup: data["reply_markup"] = reply_markup
        return self._request("sendInvoice", data)
    
    def answer_shipping_query(self, shipping_query_id: str, ok: bool,
                             shipping_options: List[dict] = None,
                             error_message: str = None) -> dict:
        data = {"shipping_query_id": shipping_query_id, "ok": ok}
        if shipping_options: data["shipping_options"] = shipping_options
        if error_message: data["error_message"] = error_message
        return self._request("answerShippingQuery", data)
    
    def answer_pre_checkout_query(self, pre_checkout_query_id: str, ok: bool,
                                  error_message: str = None) -> dict:
        data = {"pre_checkout_query_id": pre_checkout_query_id, "ok": ok}
        if error_message: data["error_message"] = error_message
        return self._request("answerPreCheckoutQuery", data)
    
    def create_invoice_link(self, title: str, description: str, payload: str,
                           provider_token: str, currency: str, prices: List[dict]) -> dict:
        return self._request("createInvoiceLink", {
            "title": title, "description": description, "payload": payload,
            "provider_token": provider_token, "currency": currency, "prices": prices
        })
    
    def create_new_sticker_set(self, user_id: int, name: str, title: str,
                              png_sticker: str = None, emojis: str = None) -> dict:
        data = {"user_id": user_id, "name": name, "title": title}
        if png_sticker:
            if os.path.isfile(png_sticker):
                return self._send_file("createNewStickerSet", data, "png_sticker", png_sticker)
            data["png_sticker"] = png_sticker
        if emojis: data["emojis"] = emojis
        return self._request("createNewStickerSet", data)
    
    def add_sticker_to_set(self, user_id: int, name: str, png_sticker: str,
                           emojis: str = None) -> dict:
        data = {"user_id": user_id, "name": name}
        if os.path.isfile(png_sticker):
            return self._send_file("addStickerToSet", data, "png_sticker", png_sticker)
        data["png_sticker"] = png_sticker
        if emojis: data["emojis"] = emojis
        return self._request("addStickerToSet", data)
    
    def set_sticker_position_in_set(self, sticker: str, position: int) -> dict:
        return self._request("setStickerPositionInSet", {"sticker": sticker, "position": position})
    
    def delete_sticker_from_set(self, sticker: str) -> dict:
        return self._request("deleteStickerFromSet", {"sticker": sticker})
    
    def create_forum_topic(self, chat_id: int, name: str, icon_color: int = None) -> dict:
        data = {"chat_id": chat_id, "name": name}
        if icon_color: data["icon_color"] = icon_color
        return self._request("createForumTopic", data)
    
    def edit_forum_topic(self, chat_id: int, message_thread_id: int,
                         name: str = None) -> dict:
        data = {"chat_id": chat_id, "message_thread_id": message_thread_id}
        if name: data["name"] = name
        return self._request("editForumTopic", data)
    
    def close_forum_topic(self, chat_id: int, message_thread_id: int) -> dict:
        return self._request("closeForumTopic", {"chat_id": chat_id, "message_thread_id": message_thread_id})
    
    def delete_forum_topic(self, chat_id: int, message_thread_id: int) -> dict:
        return self._request("deleteForumTopic", {"chat_id": chat_id, "message_thread_id": message_thread_id})
    
    def set_message_reaction(self, chat_id: int, message_id: int, emoji: str = None) -> dict:
        reaction = []
        if emoji:
            reaction = [{"type": "emoji", "emoji": emoji}]
        return self._request("setMessageReaction", {
            "chat_id": chat_id, "message_id": message_id, "reaction": reaction
        })
    
    def report_spam_chat(self, chat_id: int) -> dict:
        return self._request("reportSpamChat", {"chat_id": chat_id})
    
    def report_spam_message(self, chat_id: int, message_id: int) -> dict:
        return self._request("reportSpamMessage", {"chat_id": chat_id, "message_id": message_id})


class NevitAsyncClient:
    def __init__(self, token: str, request_timeout: int = 30):
        self.token = token
        self.base_url = f"https://tapi.bale.ai/bot{token}"
        self.request_timeout = request_timeout
        self._client = httpx.AsyncClient(timeout=request_timeout)
    
    async def _request(self, method: str, data: dict = None, files: dict = None) -> dict:
        import aiohttp
        url = f"{self.base_url}/{method}"
        try:
            async with aiohttp.ClientSession() as session:
                if files:
                    async with session.post(url, data=data, files=files,
                                           timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as response:
                        return await response.json()
                else:
                    async with session.post(url, json=data,
                                           timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as response:
                        return await response.json()
        except Exception as e:
            logger.error(f"Async request error: {e}")
            return {"ok": False, "error": str(e)}
    
    async def _send_file(self, method: str, data: dict, file_key: str, file_value: str) -> dict:
        import aiohttp
        url = f"{self.base_url}/{method}"
        try:
            if os.path.isfile(file_value):
                with open(file_value, 'rb') as f:
                    files = {file_key: f.read()}
            else:
                files = {file_key: file_value}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, files=files,
                                       timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Async file upload error: {e}")
            return {"ok": False, "error": str(e)}
    
    async def approve_chat_join_request(self, chat_id: int, user_id: int) -> dict:
        return await self._request("approveChatJoinRequest", {"chat_id": chat_id, "user_id": user_id})
    
    async def decline_chat_join_request(self, chat_id: int, user_id: int) -> dict:
        return await self._request("declineChatJoinRequest", {"chat_id": chat_id, "user_id": user_id})
    
    async def get_me(self) -> dict:
        return await self._request("getMe")
    
    async def get_updates(self, offset: int = None, limit: int = 100, timeout: int = 60) -> dict:
        data = {"timeout": timeout, "limit": limit}
        if offset is not None:
            data["offset"] = offset
        return await self._request("getUpdates", data)
    
    async def get_webhook_info(self) -> dict:
        return await self._request("getWebhookInfo")
    
    async def set_webhook(self, url: str, max_connections: int = 40) -> dict:
        return await self._request("setWebhook", {"url": url, "max_connections": max_connections})
    
    async def delete_webhook(self) -> dict:
        return await self._request("deleteWebhook")
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = None,
                          disable_web_page_preview: bool = None,
                          disable_notification: bool = None,
                          reply_to_message_id: int = None,
                          reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "text": text}
        if parse_mode: data["parse_mode"] = parse_mode
        if disable_web_page_preview: data["disable_web_page_preview"] = disable_web_page_preview
        if disable_notification: data["disable_notification"] = disable_notification
        if reply_to_message_id: data["reply_to_message_id"] = reply_to_message_id
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendMessage", data)
    
    async def send_photo(self, chat_id: int, photo: str, caption: str = None,
                         parse_mode: str = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(photo):
            return await self._send_file("sendPhoto", data, "photo", photo)
        data["photo"] = photo
        if caption: data["caption"] = caption
        if parse_mode: data["parse_mode"] = parse_mode
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendPhoto", data)
    
    async def send_audio(self, chat_id: int, audio: str, caption: str = None,
                         duration: int = None, performer: str = None, title: str = None,
                         reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(audio):
            return await self._send_file("sendAudio", data, "audio", audio)
        data["audio"] = audio
        if caption: data["caption"] = caption
        if duration: data["duration"] = duration
        if performer: data["performer"] = performer
        if title: data["title"] = title
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendAudio", data)
    
    async def send_voice(self, chat_id: int, voice: str, caption: str = None,
                         duration: int = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(voice):
            return await self._send_file("sendVoice", data, "voice", voice)
        data["voice"] = voice
        if caption: data["caption"] = caption
        if duration: data["duration"] = duration
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendVoice", data)
    
    async def send_video(self, chat_id: int, video: str, caption: str = None,
                         duration: int = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(video):
            return await self._send_file("sendVideo", data, "video", video)
        data["video"] = video
        if caption: data["caption"] = caption
        if duration: data["duration"] = duration
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendVideo", data)
    
    async def send_animation(self, chat_id: int, animation: str, caption: str = None,
                             duration: int = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(animation):
            return await self._send_file("sendAnimation", data, "animation", animation)
        data["animation"] = animation
        if caption: data["caption"] = caption
        if duration: data["duration"] = duration
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendAnimation", data)
    
    async def send_document(self, chat_id: int, document: str, caption: str = None,
                           reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(document):
            return await self._send_file("sendDocument", data, "document", document)
        data["document"] = document
        if caption: data["caption"] = caption
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendDocument", data)
    
    async def send_sticker(self, chat_id: int, sticker: str, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(sticker):
            return await self._send_file("sendSticker", data, "sticker", sticker)
        data["sticker"] = sticker
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendSticker", data)
    
    async def send_location(self, chat_id: int, latitude: float, longitude: float,
                            live_period: int = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "latitude": latitude, "longitude": longitude}
        if live_period: data["live_period"] = live_period
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendLocation", data)
    
    async def send_venue(self, chat_id: int, latitude: float, longitude: float,
                        title: str, address: str, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "latitude": latitude, "longitude": longitude,
                "title": title, "address": address}
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendVenue", data)
    
    async def send_contact(self, chat_id: int, phone_number: str, first_name: str,
                          last_name: str = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "phone_number": phone_number, "first_name": first_name}
        if last_name: data["last_name"] = last_name
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendContact", data)
    
    async def send_poll(self, chat_id: int, question: str, options: List[str],
                       is_anonymous: bool = True, type: str = "regular",
                       allows_multiple_answers: bool = None,
                       reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "question": question, "options": options,
                "is_anonymous": is_anonymous, "type": type}
        if allows_multiple_answers is not None:
            data["allows_multiple_answers"] = allows_multiple_answers
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendPoll", data)
    
    async def send_dice(self, chat_id: int, emoji: str = None,
                       reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if emoji: data["emoji"] = emoji
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendDice", data)
    
    async def send_game(self, chat_id: int, game_short_name: str,
                       reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "game_short_name": game_short_name}
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("sendGame", data)
    
    async def send_media_group(self, chat_id: int, media: List[dict]) -> dict:
        return await self._request("sendMediaGroup", {"chat_id": chat_id, "media": json.dumps(media)})
    
    async def send_chat_action(self, chat_id: int, action: str) -> dict:
        return await self._request("sendChatAction", {"chat_id": chat_id, "action": action})
    
    async def forward_message(self, chat_id: int, from_chat_id: int,
                             message_id: int) -> dict:
        return await self._request("forwardMessage", {
            "chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id
        })
    
    async def copy_message(self, chat_id: int, from_chat_id: int, message_id: int,
                          caption: str = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id}
        if caption: data["caption"] = caption
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("copyMessage", data)
    
    async def delete_message(self, chat_id: int, message_id: int) -> dict:
        return await self._request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    
    async def edit_message_text(self, chat_id: int, message_id: int, text: str,
                               parse_mode: str = None, reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if parse_mode: data["parse_mode"] = parse_mode
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("editMessageText", data)
    
    async def edit_message_reply_markup(self, chat_id: int, message_id: int,
                                        reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "message_id": message_id}
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._request("editMessageReplyMarkup", data)
    
    async def answer_callback_query(self, callback_query_id: str, text: str = None,
                                   show_alert: bool = False) -> dict:
        data = {"callback_query_id": callback_query_id}
        if text: data["text"] = text
        if show_alert: data["show_alert"] = show_alert
        return await self._request("answerCallbackQuery", data)
    
    async def get_chat(self, chat_id: int) -> dict:
        return await self._request("getChat", {"chat_id": chat_id})
    
    async def get_chat_administrators(self, chat_id: int) -> dict:
        return await self._request("getChatAdministrators", {"chat_id": chat_id})
    
    async def get_chat_member(self, chat_id: int, user_id: int) -> dict:
        return await self._request("getChatMember", {"chat_id": chat_id, "user_id": user_id})
    
    async def get_chat_members_count(self, chat_id: int) -> dict:
        return await self._request("getChatMembersCount", {"chat_id": chat_id})
    
    async def kick_chat_member(self, chat_id: int, user_id: int) -> dict:
        return await self._request("kickChatMember", {"chat_id": chat_id, "user_id": user_id})
    
    async def unban_chat_member(self, chat_id: int, user_id: int) -> dict:
        return await self._request("unbanChatMember", {"chat_id": chat_id, "user_id": user_id})
    
    async def restrict_chat_member(self, chat_id: int, user_id: int,
                                    permissions: dict) -> dict:
        return await self._request("restrictChatMember", {
            "chat_id": chat_id, "user_id": user_id, "permissions": permissions
        })
    
    async def promote_chat_member(self, chat_id: int, user_id: int, **kwargs) -> dict:
        data = {"chat_id": chat_id, "user_id": user_id}
        data.update(kwargs)
        return await self._request("promoteChatMember", data)
    
    async def set_chat_title(self, chat_id: int, title: str) -> dict:
        return await self._request("setChatTitle", {"chat_id": chat_id, "title": title})
    
    async def set_chat_description(self, chat_id: int, description: str) -> dict:
        return await self._request("setChatDescription", {"chat_id": chat_id, "description": description})
    
    async def set_chat_photo(self, chat_id: int, photo: str) -> dict:
        return await self._send_file("setChatPhoto", {"chat_id": chat_id}, "photo", photo)
    
    async def delete_chat_photo(self, chat_id: int) -> dict:
        return await self._request("deleteChatPhoto", {"chat_id": chat_id})
    
    async def export_chat_invite_link(self, chat_id: int) -> dict:
        return await self._request("exportChatInviteLink", {"chat_id": chat_id})
    
    async def create_chat_invite_link(self, chat_id: int, expire_date: int = None,
                                       member_limit: int = None) -> dict:
        data = {"chat_id": chat_id}
        if expire_date: data["expire_date"] = expire_date
        if member_limit: data["member_limit"] = member_limit
        return await self._request("createChatInviteLink", data)
    
    async def leave_chat(self, chat_id: int) -> dict:
        return await self._request("leaveChat", {"chat_id": chat_id})
    
    async def pin_chat_message(self, chat_id: int, message_id: int,
                               disable_notification: bool = None) -> dict:
        data = {"chat_id": chat_id, "message_id": message_id}
        if disable_notification: data["disable_notification"] = disable_notification
        return await self._request("pinChatMessage", data)
    
    async def unpin_chat_message(self, chat_id: int, message_id: int = None) -> dict:
        data = {"chat_id": chat_id}
        if message_id: data["message_id"] = message_id
        return await self._request("unpinChatMessage", data)
    
    async def get_file(self, file_id: str) -> dict:
        return await self._request("getFile", {"file_id": file_id})
    
    async def get_file_url(self, file_id: str) -> Optional[str]:
        result = await self.get_file(file_id)
        if result.get("ok"):
            file_path = result["result"]["file_path"]
            return f"https://tapi.bale.ai/file/bot{self.token}/{file_path}"
        return None
    
    async def set_my_commands(self, commands: List[dict]) -> dict:
        return await self._request("setMyCommands", {"commands": commands})
    
    async def get_my_commands(self) -> dict:
        return await self._request("getMyCommands")
    
    async def delete_my_commands(self) -> dict:
        return await self._request("deleteMyCommands")
    
    async def answer_inline_query(self, inline_query_id: str, results: List[dict],
                                  cache_time: int = 300, next_offset: str = None) -> dict:
        data = {"inline_query_id": inline_query_id, "results": results, "cache_time": cache_time}
        if next_offset: data["next_offset"] = next_offset
        return await self._request("answerInlineQuery", data)
    
    async def set_message_reaction(self, chat_id: int, message_id: int,
                                   emoji: str = None) -> dict:
        reaction = []
        if emoji:
            reaction = [{"type": "emoji", "emoji": emoji}]
        return await self._request("setMessageReaction", {
            "chat_id": chat_id, "message_id": message_id, "reaction": reaction
        })