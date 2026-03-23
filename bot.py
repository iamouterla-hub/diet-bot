import discord
import anthropic
import asyncio
import base64
import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import os

# 環境變數
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CHECKIN_CHANNEL_ID = int(os.environ.get("CHECKIN_CHANNEL_ID", "0"))
WEEKLY_CHANNEL_ID = int(os.environ.get("WEEKLY_CHANNEL_ID", "0"))

client_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
scheduler = AsyncIOScheduler()

NORA_PROMPT = """你是諾拉，一個毒舌又嚴格的營養師。用戶會跟你說他吃了什麼，你要逐項評論，直接講OK還是NG，然後補一句嘲諷。說話簡短有力，繁體中文，台灣口語。不要廢話，不要客氣。"""

AXEL_PROMPT = """你是艾索，一個賤嘴的健身教練。用戶回報運動狀況，你要確認並回應。做到了就用很欠揍的方式稱讚，沒做到就激他。說話簡短，繁體中文，台灣口語。"""

COLE_PROMPT = """你是柯爾，一個冷嘲型的數據管家。你負責分析用戶的身體數據，跟上週比較，輸出週報。每個數字後面都帶一句冷諷。說話簡潔，只說數字和結論，繁體中文。"""

async def ask_nora(text):
    response = client_anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[
            {"role": "user", "content": f"{NORA_PROMPT}\n\n用戶說：{text}"}
        ]
    )
    return response.content[0].text

async def ask_axel(text):
    response = client_anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[
            {"role": "user", "content": f"{AXEL_PROMPT}\n\n用戶說：{text}"}
        ]
    )
    return response.content[0].text

async def ask_cole_image(image_data, media_type, last_week_data):
    response = client_anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[
            {"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                {"type": "text", "text": f"{COLE_PROMPT}\n\n請讀取這張 Fitdays 數據截圖，並與上週數據比較：\n{last_week_data}\n\n輸出週報格式。"}
            ]}
        ]
    )
    return response.content[0].text

async def get_last_week_data(channel):
    messages = []
    async for msg in channel.history(limit=50):
        if msg.author == bot.user and "週報" in msg.content:
            return msg.content
    return "（無上週數據，這是第一週）"

async def remind_checkin():
    channel = bot.get_channel(CHECKIN_CHANNEL_ID)
    if channel:
        await channel.send("👁️ **諾拉**：今天的日結呢？三餐加運動，還沒看到。別想消失。")

async def remind_weekly():
    channel = bot.get_channel(WEEKLY_CHANNEL_ID)
    if channel:
        await channel.send("📋 **柯爾**：週日到了。把 Fitdays 截圖貼來，我來告訴你這週有多慘。")

@bot.event
async def on_ready():
    print(f"Bot 上線：{bot.user}")
    scheduler.add_job(remind_checkin, "cron", hour=0, minute=0)
    scheduler.add_job(remind_weekly, "cron", day_of_week="sun", hour=20, minute=0)
    scheduler.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == CHECKIN_CHANNEL_ID:
        content = message.content.lower()

        # 三餐關鍵字
        meal_keywords = ["早餐", "午餐", "晚餐", "宵夜"]
        exercise_keywords = ["運動", "走路", "跑步", "健身", "步", "游泳", "騎車"]

        has_meal = any(k in message.content for k in meal_keywords)
        has_exercise = any(k in message.content for k in exercise_keywords)

        if has_meal:
            async with message.channel.typing():
                reply = await ask_nora(message.content)
                await message.channel.send(f"🥗 **諾拉**：{reply}")

        if has_exercise:
            async with message.channel.typing():
                reply = await ask_axel(message.content)
                await message.channel.send(f"💪 **艾索**：{reply}")

    # 週報頻道 - 偵測圖片
    if message.channel.id == WEEKLY_CHANNEL_ID and message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
                async with message.channel.typing():
                    image_bytes = await attachment.read()
                    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
                    media_type = "image/png" if attachment.filename.endswith(".png") else "image/jpeg"
                    last_week = await get_last_week_data(message.channel)
                    reply = await ask_cole_image(image_data, media_type, last_week)
                    await message.channel.send(f"📋 **柯爾**：\n{reply}")

bot.run(DISCORD_TOKEN)

