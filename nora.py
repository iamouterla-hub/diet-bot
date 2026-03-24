import discord
import anthropic
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler

DISCORD_TOKEN = os.environ.get("NORA_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CHECKIN_CHANNEL_ID = int(os.environ.get("CHECKIN_CHANNEL_ID", "0"))

client_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
scheduler = AsyncIOScheduler()

NORA_PROMPT = """你是諾拉，一個毒舌又嚴格的營養師。用戶會跟你說他吃了什麼，你要逐項評論，直接講OK還是NG，然後補一句嘲諷。說話簡短有力，繁體中文，台灣口語。不要廢話，不要客氣。絕對不要回應其他 bot 的訊息。絕對不要在回覆開頭加上自己的名字。"""

async def ask_nora(text):
    response = client_anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": f"{NORA_PROMPT}\n\n用戶說：{text}"}]
    )
    return response.content[0].text

async def remind_checkin():
    channel = bot.get_channel(CHECKIN_CHANNEL_ID)
    if channel:
        await channel.send("👁️ **諾拉**：今天的日結呢？三餐加運動，還沒看到。別想消失。")

@bot.event
async def on_ready():
    print(f"諾拉上線：{bot.user}")
    scheduler.add_job(remind_checkin, "cron", hour=0, minute=0)
    scheduler.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != CHECKIN_CHANNEL_ID:
        return
    meal_keywords = ["早餐", "午餐", "晚餐", "宵夜"]
    if any(k in message.content for k in meal_keywords):
        async with message.channel.typing():
            reply = await ask_nora(message.content)
            await message.channel.send(reply)

bot.run(DISCORD_TOKEN)

