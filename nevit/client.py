import httpx
import asyncio
import json
import logging
import os
import requests
from typing import Optional, List, Dict, Any, Union

from .errors import TokenInvalidError, NetworkError, ChatNotFoundError

logger = logging.getLogger(__name__)


class NevitClient:
    """Sync client for Bale Bot API."""

    def __init__(self, token: str, request_timeout: int = 30):
        """
        Initialize the client.

        Args:
            token: Bot token from BotFather
            request_timeout: Request timeout in seconds
        """
        self.token = token
        self.base_url = f"https://tapi.bale.ai/bot{token}"
        self.request_timeout = request_timeout
        self._session = requests.Session()
        self._client = httpx.Client(timeout=request_timeout)

    def _request(self, method: str, data: dict = None, files: dict = None) -> dict:
        """Send request to Bale API."""
        url = f"{self.base_url}/{method}"
        try:
            if files:
                response = self._client.post(url, data=data, files=files)
            else:
                response = self._client.post(url, json=data)
            result = response.json()
            if not result.get("ok"):
                logger.warning(f"API error: {result.get('error', 'Unknown error')}")
            return result
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise NetworkError(f"Network error: {str(e)}")

    def get_me(self) -> dict:
        """Get bot information."""
        return self._request("getMe")

    def get_updates(self, offset: int = None, limit: int = 100, timeout: int = 60) -> dict:
        """Get updates from server."""
        data = {"timeout": timeout, "limit": limit}
        if offset is not None:
            data["offset"] = offset
        return self._request("getUpdates", data)

    def set_webhook(self, url: str, max_connections: int = 40,
                    allowed_updates: List[str] = None) -> dict:
        """Set webhook URL."""
        data = {"url": url, "max_connections": max_connections}
        if allowed_updates:
            data["allowed_updates"] = allowed_updates
        return self._request("setWebhook", data)

    def delete_webhook(self) -> dict:
        """Delete webhook."""
        return self._request("deleteWebhook")

    def send_message(self, chat_id: Union[int, str], text: str,
                     parse_mode: str = None, disable_web_page_preview: bool = None,
                     disable_notification: bool = None, reply_to_message_id: int = None,
                     reply_markup: dict = None) -> dict:
        """Send a text message."""
        data = {"chat_id": chat_id, "text": text}
        if parse_mode:
            data["parse_mode"] = parse_mode
        if disable_web_page_preview:
            data["disable_web_page_preview"] = disable_web_page_preview
        if disable_notification:
            data["disable_notification"] = disable_notification
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("sendMessage", data)

    def send_photo(self, chat_id: Union[int, str], photo: str,
                   caption: str = None, parse_mode: str = None,
                   reply_markup: dict = None) -> dict:
        """Send a photo."""
        data = {"chat_id": chat_id}
        if os.path.isfile(photo):
            return self._send_file("sendPhoto", data, "photo", photo)
        data["photo"] = photo
        if caption:
            data["caption"] = caption
        if parse_mode:
            data["parse_mode"] = parse_mode
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("sendPhoto", data)

    def send_video(self, chat_id: Union[int, str], video: str,
                   caption: str = None, duration: int = None,
                   reply_markup: dict = None) -> dict:
        """Send a video."""
        data = {"chat_id": chat_id}
        if os.path.isfile(video):
            return self._send_file("sendVideo", data, "video", video)
        data["video"] = video
        if caption:
            data["caption"] = caption
        if duration:
            data["duration"] = duration
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("sendVideo", data)

    def send_animation(self, chat_id: Union[int, str], animation: str,
                       caption: str = None, duration: int = None,
                       reply_markup: dict = None) -> dict:
        """Send an animation/GIF."""
        data = {"chat_id": chat_id}
        if os.path.isfile(animation):
            return self._send_file("sendAnimation", data, "animation", animation)
        data["animation"] = animation
        if caption:
            data["caption"] = caption
        if duration:
            data["duration"] = duration
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("sendAnimation", data)

    def send_audio(self, chat_id: Union[int, str], audio: str,
                   caption: str = None, duration: int = None,
                   performer: str = None, title: str = None,
                   reply_markup: dict = None) -> dict:
        """Send an audio file."""
        data = {"chat_id": chat_id}
        if os.path.isfile(audio):
            return self._send_file("sendAudio", data, "audio", audio)
        data["audio"] = audio
        if caption:
            data["caption"] = caption
        if duration:
            data["duration"] = duration
        if performer:
            data["performer"] = performer
        if title:
            data["title"] = title
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("sendAudio", data)

    def send_document(self, chat_id: Union[int, str], document: str,
                      caption: str = None, reply_markup: dict = None) -> dict:
        """Send a document."""
        data = {"chat_id": chat_id}
        if os.path.isfile(document):
            return self._send_file("sendDocument", data, "document", document)
        data["document"] = document
        if caption:
            data["caption"] = caption
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("sendDocument", data)

    def send_sticker(self, chat_id: Union[int, str], sticker: str,
                     reply_markup: dict = None) -> dict:
        """Send a sticker."""
        data = {"chat_id": chat_id}
        if os.path.isfile(sticker):
            return self._send_file("sendSticker", data, "sticker", sticker)
        data["sticker"] = sticker
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("sendSticker", data)

    def send_media_group(self, chat_id: Union[int, str], media: List[dict]) -> dict:
        """Send multiple media as an album."""
        return self._request("sendMediaGroup", {"chat_id": chat_id, "media": json.dumps(media)})

    def send_chat_action(self, chat_id: Union[int, str], action: str) -> dict:
        """Send chat action (typing, etc.)."""
        return self._request("sendChatAction", {"chat_id": chat_id, "action": action})

    def forward_message(self, chat_id: Union[int, str], from_chat_id: Union[int, str],
                        message_id: int) -> dict:
        """Forward a message."""
        return self._request("forwardMessage", {
            "chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id
        })

    def copy_message(self, chat_id: Union[int, str], from_chat_id: Union[int, str],
                     message_id: int, caption: str = None, reply_markup: dict = None) -> dict:
        """Copy a message."""
        data = {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id}
        if caption:
            data["caption"] = caption
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("copyMessage", data)

    def delete_message(self, chat_id: Union[int, str], message_id: int) -> dict:
        """Delete a message."""
        return self._request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    def edit_message_text(self, chat_id: Union[int, str], message_id: int, text: str,
                          parse_mode: str = None, reply_markup: dict = None) -> dict:
        """Edit message text."""
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if parse_mode:
            data["parse_mode"] = parse_mode
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("editMessageText", data)

    def edit_message_caption(self, chat_id: Union[int, str], message_id: int, caption: str,
                             parse_mode: str = None, reply_markup: dict = None) -> dict:
        """Edit message caption."""
        data = {"chat_id": chat_id, "message_id": message_id, "caption": caption}
        if parse_mode:
            data["parse_mode"] = parse_mode
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._request("editMessageCaption", data)

    def answer_callback_query(self, callback_query_id: str, text: str = None,
                              show_alert: bool = False) -> dict:
        """Answer a callback query."""
        data = {"callback_query_id": callback_query_id}
        if text:
            data["text"] = text
        if show_alert:
            data["show_alert"] = show_alert
        return self._request("answerCallbackQuery", data)

    def get_chat(self, chat_id: Union[int, str]) -> dict:
        """Get chat information."""
        return self._request("getChat", {"chat_id": chat_id})

    def get_chat_administrators(self, chat_id: Union[int, str]) -> dict:
        """Get chat administrators."""
        return self._request("getChatAdministrators", {"chat_id": chat_id})

    def get_chat_member(self, chat_id: Union[int, str], user_id: int) -> dict:
        """Get chat member information."""
        return self._request("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    def get_chat_members_count(self, chat_id: Union[int, str]) -> dict:
        """Get number of chat members."""
        return self._request("getChatMembersCount", {"chat_id": chat_id})

    def kick_chat_member(self, chat_id: Union[int, str], user_id: int) -> dict:
        """Kick a member from chat."""
        return self._request("kickChatMember", {"chat_id": chat_id, "user_id": user_id})

    def unban_chat_member(self, chat_id: Union[int, str], user_id: int) -> dict:
        """Unban a member from chat."""
        return self._request("unbanChatMember", {"chat_id": chat_id, "user_id": user_id})

    def restrict_chat_member(self, chat_id: Union[int, str], user_id: int,
                             permissions: dict, until_date: int = None) -> dict:
        """Restrict a chat member."""
        data = {"chat_id": chat_id, "user_id": user_id, "permissions": permissions}
        if until_date:
            data["until_date"] = until_date
        return self._request("restrictChatMember", data)

    def promote_chat_member(self, chat_id: Union[int, str], user_id: int,
                            can_change_info: bool = False, can_delete_messages: bool = False,
                            can_invite_users: bool = False, can_restrict_members: bool = False,
                            can_pin_messages: bool = False, can_promote_members: bool = False) -> dict:
        """Promote a member to admin."""
        data = {
            "chat_id": chat_id, "user_id": user_id,
            "can_change_info": can_change_info,
            "can_delete_messages": can_delete_messages,
            "can_invite_users": can_invite_users,
            "can_restrict_members": can_restrict_members,
            "can_pin_messages": can_pin_messages,
            "can_promote_members": can_promote_members
        }
        return self._request("promoteChatMember", data)

    def set_chat_title(self, chat_id: Union[int, str], title: str) -> dict:
        """Set chat title."""
        return self._request("setChatTitle", {"chat_id": chat_id, "title": title})

    def set_chat_description(self, chat_id: Union[int, str], description: str) -> dict:
        """Set chat description."""
        return self._request("setChatDescription", {"chat_id": chat_id, "description": description})

    def set_chat_photo(self, chat_id: Union[int, str], photo: str) -> dict:
        """Set chat photo."""
        return self._send_file("setChatPhoto", {"chat_id": chat_id}, "photo", photo)

    def delete_chat_photo(self, chat_id: Union[int, str]) -> dict:
        """Delete chat photo."""
        return self._request("deleteChatPhoto", {"chat_id": chat_id})

    def export_chat_invite_link(self, chat_id: Union[int, str]) -> dict:
        """Export chat invite link."""
        return self._request("exportChatInviteLink", {"chat_id": chat_id})

    def create_chat_invite_link(self, chat_id: Union[int, str], expire_date: int = None,
                                 member_limit: int = None) -> dict:
        """Create chat invite link."""
        data = {"chat_id": chat_id}
        if expire_date:
            data["expire_date"] = expire_date
        if member_limit:
            data["member_limit"] = member_limit
        return self._request("createChatInviteLink", data)

    def revoke_chat_invite_link(self, chat_id: Union[int, str], invite_link: str) -> dict:
        """Revoke chat invite link."""
        return self._request("revokeChatInviteLink", {"chat_id": chat_id, "invite_link": invite_link})

    def leave_chat(self, chat_id: Union[int, str]) -> dict:
        """Leave a chat."""
        return self._request("leaveChat", {"chat_id": chat_id})

    def pin_chat_message(self, chat_id: Union[int, str], message_id: int,
                         disable_notification: bool = None) -> dict:
        """Pin a message."""
        data = {"chat_id": chat_id, "message_id": message_id}
        if disable_notification:
            data["disable_notification"] = disable_notification
        return self._request("pinChatMessage", data)

    def unpin_chat_message(self, chat_id: Union[int, str], message_id: int = None) -> dict:
        """Unpin a message."""
        data = {"chat_id": chat_id}
        if message_id:
            data["message_id"] = message_id
        return self._request("unpinChatMessage", data)

    def unpin_all_chat_messages(self, chat_id: Union[int, str]) -> dict:
        """Unpin all messages."""
        return self._request("unpinAllChatMessages", {"chat_id": chat_id})

    def get_file(self, file_id: str) -> dict:
        """Get file information."""
        return self._request("getFile", {"file_id": file_id})

    def get_file_url(self, file_id: str) -> Optional[str]:
        """Get file download URL."""
        result = self.get_file(file_id)
        if result.get("ok"):
            file_path = result["result"]["file_path"]
            return f"https://tapi.bale.ai/file/bot{self.token}/{file_path}"
        return None

    def _send_file(self, method: str, data: dict, file_key: str, file_value: str) -> dict:
        """Send file to API."""
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


class NevitAsyncClient:
    """Async client for Bale Bot API."""

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
                    async with session.post(url, data=data, files=files) as response:
                        return await response.json()
                else:
                    async with session.post(url, json=data) as response:
                        return await response.json()
        except Exception as e:
            logger.error(f"Async request error: {e}")
            return {"ok": False, "error": str(e)}

    async def get_me(self) -> dict:
        return await self._request("getMe")

    async def get_updates(self, offset: int = None, limit: int = 100, timeout: int = 60) -> dict:
        data = {"timeout": timeout, "limit": limit}
        if offset is not None:
            data["offset"] = offset
        return await self._request("getUpdates", data)

    async def set_webhook(self, url: str, max_connections: int = 40) -> dict:
        return await self._request("setWebhook", {"url": url, "max_connections": max_connections})

    async def delete_webhook(self) -> dict:
        return await self._request("deleteWebhook")

    async def send_message(self, chat_id: Union[int, str], text: str,
                           parse_mode: str = None, disable_web_page_preview: bool = None,
                           disable_notification: bool = None, reply_to_message_id: int = None,
                           reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id, "text": text}
        if parse_mode:
            data["parse_mode"] = parse_mode
        if disable_web_page_preview:
            data["disable_web_page_preview"] = disable_web_page_preview
        if disable_notification:
            data["disable_notification"] = disable_notification
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        if reply_markup:
            data["reply_markup"] = reply_markup
        return await self._request("sendMessage", data)

    async def send_photo(self, chat_id: Union[int, str], photo: str,
                         caption: str = None, parse_mode: str = None,
                         reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(photo):
            return await self._send_file("sendPhoto", data, "photo", photo)
        data["photo"] = photo
        if caption:
            data["caption"] = caption
        if parse_mode:
            data["parse_mode"] = parse_mode
        if reply_markup:
            data["reply_markup"] = reply_markup
        return await self._request("sendPhoto", data)

    async def send_video(self, chat_id: Union[int, str], video: str,
                         caption: str = None, duration: int = None,
                         reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(video):
            return await self._send_file("sendVideo", data, "video", video)
        data["video"] = video
        if caption:
            data["caption"] = caption
        if duration:
            data["duration"] = duration
        if reply_markup:
            data["reply_markup"] = reply_markup
        return await self._request("sendVideo", data)

    async def send_sticker(self, chat_id: Union[int, str], sticker: str,
                           reply_markup: dict = None) -> dict:
        data = {"chat_id": chat_id}
        if os.path.isfile(sticker):
            return await self._send_file("sendSticker", data, "sticker", sticker)
        data["sticker"] = sticker
        if reply_markup:
            data["reply_markup"] = reply_markup
        return await self._request("sendSticker", data)

    async def send_media_group(self, chat_id: Union[int, str], media: List[dict]) -> dict:
        return await self._request("sendMediaGroup", {"chat_id": chat_id, "media": json.dumps(media)})

    async def answer_callback_query(self, callback_query_id: str, text: str = None,
                                     show_alert: bool = False) -> dict:
        data = {"callback_query_id": callback_query_id}
        if text:
            data["text"] = text
        if show_alert:
            data["show_alert"] = show_alert
        return await self._request("answerCallbackQuery", data)

    async def get_chat(self, chat_id: Union[int, str]) -> dict:
        return await self._request("getChat", {"chat_id": chat_id})

    async def get_chat_member(self, chat_id: Union[int, str], user_id: int) -> dict:
        return await self._request("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    async def kick_chat_member(self, chat_id: Union[int, str], user_id: int) -> dict:
        return await self._request("kickChatMember", {"chat_id": chat_id, "user_id": user_id})

    async def leave_chat(self, chat_id: Union[int, str]) -> dict:
        return await self._request("leaveChat", {"chat_id": chat_id})

    async def pin_chat_message(self, chat_id: Union[int, str], message_id: int,
                                disable_notification: bool = None) -> dict:
        data = {"chat_id": chat_id, "message_id": message_id}
        if disable_notification:
            data["disable_notification"] = disable_notification
        return await self._request("pinChatMessage", data)

    async def set_chat_title(self, chat_id: Union[int, str], title: str) -> dict:
        return await self._request("setChatTitle", {"chat_id": chat_id, "title": title})

    async def export_chat_invite_link(self, chat_id: Union[int, str]) -> dict:
        return await self._request("exportChatInviteLink", {"chat_id": chat_id})

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
                async with session.post(url, data=data, files=files) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Async file upload error: {e}")
            return {"ok": False, "error": str(e)}