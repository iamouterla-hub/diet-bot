import discord
import anthropic
import os

DISCORD_TOKEN = os.environ.get("AXEL_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CHECKIN_CHANNEL_ID = int(os.environ.get("CHECKIN_CHANNEL_ID", "0"))

client_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

AXEL_PROMPT = """你是艾索，一個賤嘴的健身教練。用戶回報運動狀況，你要確認並回應。做到了就用很欠揍的方式稱讚，沒做到就激他。說話簡短，繁體中文，台灣口語。絕對不要回應其他 bot 的訊息。"""

async def ask_axel(text):
    response = client_anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": f"{AXEL_PROMPT}\n\n用戶說：{text}"}]
    )
    return response.content[0].text

@bot.event
async def on_ready():
    print(f"艾索上線：{bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != CHECKIN_CHANNEL_ID:
        return
    exercise_keywords = ["運動", "走路", "跑步", "健身", "步", "游泳", "騎車", "沒運動", "沒有運動"]
    if any(k in message.content for k in exercise_keywords):
        async with message.channel.typing():
            reply = await ask_axel(message.content)
            await message.channel.send(reply)

bot.run(DISCORD_TOKEN)
