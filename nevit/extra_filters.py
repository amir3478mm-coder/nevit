from .types import Message

def payment_successful(message: Message) -> bool:
    return hasattr(message, 'successful_payment') and message.successful_payment is not None

def exact_match(target_text: str):
    def checker(message: Message) -> bool:
        if not message.text:
            return False
        return message.text == target_text
    return checker

def get_message_content(message: Message):
    if message.text:
        return {"type": "text", "value": message.text}
    if hasattr(message, 'photo') and message.photo:
        return {"type": "photo", "value": message.photo}
    if hasattr(message, 'video') and message.video:
        return {"type": "video", "value": message.video}
    if hasattr(message, 'animation') and message.animation:
        return {"type": "animation", "value": message.animation}
    if hasattr(message, 'sticker') and message.sticker:
        return {"type": "sticker", "value": message.sticker}
    if hasattr(message, 'document') and message.document:
        return {"type": "document", "value": message.document}
    if hasattr(message, 'voice') and message.voice:
        return {"type": "voice", "value": message.voice}
    if hasattr(message, 'audio') and message.audio:
        return {"type": "audio", "value": message.audio}
    if hasattr(message, 'location') and message.location:
        return {"type": "location", "value": message.location}
    if hasattr(message, 'venue') and message.venue:
        return {"type": "venue", "value": message.venue}
    if hasattr(message, 'contact') and message.contact:
        return {"type": "contact", "value": message.contact}
    if hasattr(message, 'poll') and message.poll:
        return {"type": "poll", "value": message.poll}
    if hasattr(message, 'dice') and message.dice:
        return {"type": "dice", "value": message.dice}
    if hasattr(message, 'game') and message.game:
        return {"type": "game", "value": message.game}
    if hasattr(message, 'invoice') and message.invoice:
        return {"type": "invoice", "value": message.invoice}
    if hasattr(message, 'successful_payment') and message.successful_payment:
        return {"type": "successful_payment", "value": message.successful_payment}
    if hasattr(message, 'new_chat_members') and message.new_chat_members:
        return {"type": "new_chat_members", "value": message.new_chat_members}
    if hasattr(message, 'left_chat_member') and message.left_chat_member:
        return {"type": "left_chat_member", "value": message.left_chat_member}
    return {"type": "unknown", "value": None}