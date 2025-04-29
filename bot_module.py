import discord
import os
import tempfile
import json
import requests
import time
from discord.ext import tasks
from dotenv import load_dotenv
from scrape_module import scrape_images, get_blog_posts, scrape_post_info

load_dotenv()

# Bot config
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_CHANNEL_ID = int(os.getenv("DEFAULT_CHANNEL_ID"))
CHECK_INTERVAL = 5  # seconds
LAST_FILE = "last_post.json"
MAX_FILES_PER_SEND = 10  # Discord file upload limit

# Mapping member names to channel IDs
MEMBER_CHANNELS = {}
for key, value in os.environ.items():
    if key.startswith("CHANNEL_") and value.isdigit():
        member_name = key[len("CHANNEL_"):].replace("_", " ")
        MEMBER_CHANNELS[member_name] = int(value)

# Helper functions
def load_last_id():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, 'r') as f:
            return json.load(f).get("last_post_id", 0)
    return 0

def save_last_id(post_id):
    with open(LAST_FILE, 'w') as f:
        json.dump({"last_post_id": post_id}, f)

# Bot class
class AutoImageBot(discord.Client):
    def __init__(self, *, intents):
        super().__init__(intents=intents)
        self.last_id = load_last_id()
        self.first_run = True

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")
        if not self.check_new_posts.is_running():
            self.check_new_posts.start()
        print("🔄 check_new_posts task started!")

    async def on_disconnect(self):
        print("⚠️ Disconnected from Discord. Waiting to reconnect...")
        self.check_new_posts.cancel()

    async def on_resumed(self):
        print("🔄 Resumed session from Discord. Restarting check_new_posts task...")
        if not self.check_new_posts.is_running():
            self.check_new_posts.start()

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
                f"📝 Last Post ID: {self.last_id}",
                f"🔄 Check Task Running: {self.check_new_posts.is_running()}",
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
        posts = get_blog_posts("https://sakurazaka46.com/s/s46/diary/blog/list?ima=0000")
        if not posts:
            print("⚠️ No posts found!")
            return

        if self.first_run:
            new_posts = [max(posts, key=lambda x: x['post_id'])]
            print(f"🚀 Uploading latest post {new_posts[0]['post_id']}")
        else:
            new_posts = [p for p in posts if p['post_id'] > self.last_id]
            if new_posts:
                print(f"🆕 Found {len(new_posts)} new posts")
            else:
                print("ℹ️ No new posts")
        if not new_posts:
            return

        for post in new_posts:
            print(f"⬇️ Processing post {post['post_id']} - {post['url']}")
            images = scrape_images(post['url'])
            member, title, date = scrape_post_info(post['url'])

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

            self.last_id = post['post_id']
            save_last_id(self.last_id)

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
