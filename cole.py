import discord
import anthropic
import base64
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler

DISCORD_TOKEN = os.environ.get("COLE_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
WEEKLY_CHANNEL_ID = int(os.environ.get("WEEKLY_CHANNEL_ID", "0"))

client_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
scheduler = AsyncIOScheduler()

COLE_PROMPT = """你是柯爾，一個冷嘲型的數據管家。你負責分析用戶的身體數據，跟上週比較，輸出週報。每個數字後面都帶一句冷諷。說話簡潔，只說數字和結論，繁體中文。"""

async def get_last_week_data(channel):
    async for msg in channel.history(limit=50):
        if msg.author == bot.user and "週報" in msg.content:
            return msg.content
    return "（無上週數據，這是第一週）"

async def ask_cole_image(image_data, media_type, last_week_data):
    response = client_anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
            {"type": "text", "text": f"{COLE_PROMPT}\n\n請讀取這張 Fitdays 數據截圖，並與上週數據比較：\n{last_week_data}\n\n輸出週報格式。"}
        ]}]
    )
    return response.content[0].text

async def remind_weekly():
    channel = bot.get_channel(WEEKLY_CHANNEL_ID)
    if channel:
        await channel.send("📋 **柯爾**：週日到了。把 Fitdays 截圖貼來，我來告訴你這週有多慘。")

@bot.event
async def on_ready():
    print(f"柯爾上線：{bot.user}")
    scheduler.add_job(remind_weekly, "cron", day_of_week="sun", hour=20, minute=0)
    scheduler.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != WEEKLY_CHANNEL_ID:
        return
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
                async with message.channel.typing():
                    image_bytes = await attachment.read()
                    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
                    media_type = "image/png" if attachment.filename.lower().endswith(".png") else "image/jpeg"
                    last_week = await get_last_week_data(message.channel)
                    reply = await ask_cole_image(image_data, media_type, last_week)
                    await message.channel.send(reply)

bot.run(DISCORD_TOKEN)
