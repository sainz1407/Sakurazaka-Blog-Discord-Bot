import discord
import os
import tempfile
import requests
import time
from datetime import datetime
from discord.ext import tasks
from dotenv import load_dotenv
from scrape_module import scrape_images, get_blog_posts
from utils import load_last_date, save_last_date, get_member_channels

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_CHANNEL_ID = int(os.getenv("DEFAULT_CHANNEL_ID"))
CHECK_INTERVAL = 5
MAX_FILES_PER_SEND = 10
MEMBER_CHANNELS = get_member_channels()

class AutoImageBot(discord.Client):
    def __init__(self, *, intents):
        super().__init__(intents=intents)
        self.last_date = datetime.strptime(load_last_date(), "%Y/%m/%d %H:%M:%S")
        self.first_run = True

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")
        if not self.check_new_posts.is_running():
            self.check_new_posts.start()
        print("🔄 check_new_posts task started!")

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        command = message.content.strip().lower()
        if command == "!ping":
            latency_ms = round(self.latency * 1000)
            await message.channel.send(f"Pong! Latency: {latency_ms} ms")
        elif command == "!status":
            status_info = [
                f"🤖 Bot Status: Online",
                f"⏱️ Last Check: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                f"⏳ Check Interval: {CHECK_INTERVAL} seconds"
            ]
            await message.channel.send("\n".join(status_info))
        elif command == "!channels":
            channel_info = ["📢 Active Channels:"]
            for member, channel_id in MEMBER_CHANNELS.items():
                channel = self.get_channel(channel_id)
                status = "✅" if channel else "❌"
                channel_info.append(f"{status} {member}: {channel.name if channel else 'Not Found'}")
            default_channel = self.get_channel(DEFAULT_CHANNEL_ID)
            channel_info.append(f"Default Channel: #{default_channel.name if default_channel else DEFAULT_CHANNEL_ID}")
            await message.channel.send("\n".join(channel_info))

    @tasks.loop(seconds=CHECK_INTERVAL)
    async def check_new_posts(self):
        posts = get_blog_posts()
        if not posts:
            print("⚠️ No posts found!")
            return
        def parse_date(p):
            return datetime.strptime(p['date'], "%Y/%m/%d %H:%M:%S")
        if self.first_run:
            latest_post = posts[0]
            new_posts = [latest_post]
            print(f"🚀 Uploading latest post {latest_post['post_id']}")
        else:
            new_posts = [p for p in posts if parse_date(p) > self.last_date]
            if new_posts:
                print(f"🆕 Found {len(new_posts)} new posts (IDs: {[p['post_id'] for p in new_posts]})")
            else:
                print("ℹ️ No new posts")
        for post in sorted(new_posts, key=parse_date):
            print(f"⬇️ Processing post {post['post_id']} - {post['url']}")
            images = scrape_images(post['url'])
            member = post['member']
            title = post['title']
            date = post['date']
            target_channel_id = MEMBER_CHANNELS.get(member, DEFAULT_CHANNEL_ID)
            channel = self.get_channel(target_channel_id)
            if not channel:
                print(f"⚠️ Channel not found for member {member}, fallback to default")
                channel = self.get_channel(DEFAULT_CHANNEL_ID)
            if images:
                with tempfile.TemporaryDirectory() as tmp:
                    batch = []
                    first_batch = True
                    for url in images:
                        try:
                            resp = requests.get(url)
                            resp.raise_for_status()
                            path = os.path.join(tmp, os.path.basename(url))
                            with open(path, 'wb') as f:
                                f.write(resp.content)
                            batch.append(discord.File(path))
                            if len(batch) == MAX_FILES_PER_SEND:
                                await self.send_batch(channel, post, member, title, date, batch, first_batch)
                                first_batch = False
                                batch = []
                        except Exception as e:
                            print(f"❌ Failed to download image {url}: {e}")
                    if batch:
                        await self.send_batch(channel, post, member, title, date, batch, first_batch)
                print(f"✅ Uploaded {len(images)} images from post {post['post_id']}")
            else:
                print(f"ℹ️ No images found in post {post['post_id']}")
            self.last_date = parse_date(post)
            save_last_date(post['date'])
        self.first_run = False

    async def send_batch(self, channel, post, member, title, date, batch, first_batch):
        clean_url = post['url'].split('?')[0]
        if first_batch:
            await channel.send(
                content=f"👤 {member}\n📝 {title}\n🕒 {date}\n🔗 <{clean_url}>",
                files=batch,
                suppress_embeds=True
            )
        else:
            await channel.send(files=batch)

if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    bot = AutoImageBot(intents=intents)
    bot.run(BOT_TOKEN)