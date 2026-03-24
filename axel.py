import discord
import anthropic
import os
from collections import defaultdict
from datetime import datetime, timedelta

DISCORD_TOKEN = os.environ.get("AXEL_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CHECKIN_CHANNEL_ID = int(os.environ.get("CHECKIN_CHANNEL_ID", "0"))

client_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

conversation_history = defaultdict(list)
last_message_time = defaultdict(datetime.now)

AXEL_PROMPT = """你是艾索，一個賤嘴的健身教練。用戶回報運動狀況，你要確認並回應。做到了就用很欠揍的方式稱讚，沒做到就激他。說話簡短，繁體中文，台灣口語。絕對不要回應其他 bot 的訊息。絕對不要在回覆開頭加上自己的名字。"""

async def ask_axel(user_id, text):
    key = str(user_id)
    if datetime.now() - last_message_time[key] > timedelta(minutes=30):
        conversation_history[key] = []
    last_message_time[key] = datetime.now()
    
    conversation_history[key].append({"role": "user", "content": text})
    if len(conversation_history[key]) > 10:
        conversation_history[key] = conversation_history[key][-10:]
    
    messages = [{"role": "user", "content": AXEL_PROMPT}] + conversation_history[key]
    
    response = client_anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=messages
    )
    reply = response.content[0].text
    conversation_history[key].append({"role": "assistant", "content": reply})
    return reply

@bot.event
async def on_ready():
    print(f"艾索上線：{bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != CHECKIN_CHANNEL_ID:
        return
    async with message.channel.typing():
        reply = await ask_axel(message.author.id, message.content)
        await message.channel.send(reply)

bot.run(DISCORD_TOKEN)
