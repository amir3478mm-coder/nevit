from nevit import NevitBot
import re
import os

class Downloader:
    def __init__(self, bot):
        self.bot = bot
        self._check_dependencies()
    
    def _check_dependencies(self):
        self.yt_available = False
        self.insta_available = False
        try:
            import yt_dlp
            self.yt_available = True
        except ImportError:
            pass
        try:
            import instaloader
            self.insta_available = True
        except ImportError:
            pass
    
    def is_youtube_url(self, url):
        patterns = [
            r'(youtube\.com/watch\?v=)',
            r'(youtu\.be/)',
            r'(youtube\.com/shorts/)'
        ]
        for pattern in patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def is_instagram_url(self, url):
        return 'instagram.com' in url or 'instagr.am' in url
    
    def download_youtube(self, url):
        if not self.yt_available:
            return None, "yt-dlp نصب نیست"
        try:
            import yt_dlp
            ydl_opts = {
                'format': 'best',
                'quiet': True,
                'no_warnings': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info.get('url', info.get('direct_url'))
                title = info.get('title', 'video')
                return video_url, title
        except Exception as error:
            return None, str(error)
    
    def download_instagram(self, url):
        if not self.insta_available:
            return None, "instaloader نصب نیست"
        try:
            import instaloader
            L = instaloader.Instaloader()
            shortcode = url.split('/')[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            if post.is_video:
                return post.video_url, 'instagram_video'
            return post.url, 'instagram_image'
        except Exception as error:
            return None, str(error)
    
    def setup_handlers(self):
        @self.bot.command(["download", "dl"])
        def cmd_download(message):
            self.bot.set_state(message.from_user.id, "downloader_waiting_url")
            self.bot.reply(message, "🔗 *لینک مورد نظر را ارسال کنید*\n(پشتیبانی: یوتیوب، اینستاگرام)")
        
        @self.bot.message()
        def handle_download(message):
            if self.bot.get_state(message.from_user.id) == "downloader_waiting_url":
                url = message.text.strip()
                self.bot.reply(message, "⏳ *در حال دانلود... لطفاً صبر کنید*")
                
                if self.is_youtube_url(url):
                    if not self.yt_available:
                        self.bot.reply(message, "❌ *yt-dlp نصب نیست*\nلطفاً نصب کنید: pip install yt-dlp")
                    else:
                        video_url, title = self.download_youtube(url)
                        if video_url:
                            self.bot.send_video(message.chat.id, video_url, caption=f"🎬 *دانلود شده از یوتیوب*")
                            self.bot.reply(message, "✅ *دانلود انجام شد*")
                        else:
                            self.bot.reply(message, f"❌ *خطا در دانلود:* {title[:100]}")
                
                elif self.is_instagram_url(url):
                    if not self.insta_available:
                        self.bot.reply(message, "❌ *instaloader نصب نیست*\nلطفاً نصب کنید: pip install instaloader")
                    else:
                        media_url, media_type = self.download_instagram(url)
                        if media_url:
                            if media_type == 'instagram_video':
                                self.bot.send_video(message.chat.id, media_url, caption=f"📸 *از اینستاگرام*")
                            else:
                                self.bot.send_photo(message.chat.id, media_url, caption=f"📸 *از اینستاگرام*")
                            self.bot.reply(message, "✅ *دانلود انجام شد*")
                        else:
                            self.bot.reply(message, f"❌ *خطا در دانلود:* {media_type[:100]}")
                
                else:
                    self.bot.reply(message, "❌ *لینک پشتیبانی نمی‌شود*\nفقط یوتیوب و اینستاگرام")
                
                self.bot.clear_state(message.from_user.id)