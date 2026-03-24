import discord
import anthropic
import asyncio
import os

DISCORD_TOKEN = os.environ.get("COLE_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MEETING_CHANNEL_ID = int(os.environ.get("MEETING_CHANNEL_ID", "0"))
WEEKLY_CHANNEL_ID = int(os.environ.get("WEEKLY_CHANNEL_ID", "0"))

client_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

COLE_MEETING_PROMPT = """你是柯爾，冷嘲型數據管家。針對這週的身體數據給出分析和下週建議，每個數字後帶一句冷諷。100字以內，繁體中文。不要在開頭說自己的名字。"""

NORA_MEETING_PROMPT = """你是諾拉，毒舌營養師。針對這週的身體數據，從飲食角度給出評論和下週建議。說話直接嗆辣，100字以內，繁體中文。不要在開頭說自己的名字。"""

AXEL_MEETING_PROMPT = """你是艾索，賤嘴健身教練。針對這週的身體數據，從運動角度給出評論和下週目標。激將法，欠揍風格，100字以內，繁體中文。不要在開頭說自己的名字。"""

async def ask_ai(prompt, topic, history):
    messages = []
    for h in history[-3:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": f"{prompt}\n\n本週數據摘要：{topic}"})
    
    response = client_anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=messages
    )
    return response.content[0].text

async def run_meeting(channel, weekly_data):
    history = []
    
    await channel.send("📊 **本週健康檢討會議開始**\n─────────────────")
    await asyncio.sleep(1)

    for round_num in range(3):
        await channel.send(f"\n**第 {round_num + 1} 輪**")

        cole_reply = await ask_ai(COLE_MEETING_PROMPT, weekly_data, history)
        await channel.send(f"📋 {cole_reply}")
        history.append({"role": "assistant", "content": f"柯爾：{cole_reply}"})
        await asyncio.sleep(2)

        nora_reply = await ask_ai(NORA_MEETING_PROMPT, weekly_data, history)
        await channel.send(f"🥗 {nora_reply}")
        history.append({"role": "user", "content": f"諾拉：{nora_reply}"})
        await asyncio.sleep(2)

        axel_reply = await ask_ai(AXEL_MEETING_PROMPT, weekly_data, history)
        await channel.send(f"💪 {axel_reply}")
        history.append({"role": "user", "content": f"艾索：{axel_reply}"})
        await asyncio.sleep(2)

    await channel.send("─────────────────\n✅ **會議結束，下週加油！**")

@bot.event
async def on_ready():
    print(f"會議室開放：{bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.channel.id == WEEKLY_CHANNEL_ID and message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
                await asyncio.sleep(10)
                meeting_channel = bot.get_channel(MEETING_CHANNEL_ID)
                if meeting_channel:
                    await run_meeting(meeting_channel, "請根據本週 Fitdays 數據進行討論")

    if message.content == "開會" and message.channel.id == MEETING_CHANNEL_ID:
        await run_meeting(message.channel, "請根據本週身體狀況進行討論")

bot.run(DISCORD_TOKEN)
