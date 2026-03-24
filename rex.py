import discord
import anthropic
import asyncio
import os

REX_TOKEN = os.environ.get("REX_TOKEN")
NORA_TOKEN = os.environ.get("NORA_TOKEN")
AXEL_TOKEN = os.environ.get("AXEL_TOKEN")
COLE_TOKEN = os.environ.get("COLE_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MEETING_CHANNEL_ID = int(os.environ.get("MEETING_CHANNEL_ID", "0"))
WEEKLY_CHANNEL_ID = int(os.environ.get("WEEKLY_CHANNEL_ID", "0"))

client_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

rex_bot = discord.Client(intents=intents)
nora_bot = discord.Client(intents=intents)
axel_bot = discord.Client(intents=intents)
cole_bot = discord.Client(intents=intents)

COLE_MEETING_PROMPT = """你是柯爾，冷嘲型數據管家。針對這週的身體數據給出分析和下週建議，每個數字後帶一句冷諷。50字以內，繁體中文。不要在開頭說自己的名字。不要用括號描述動作，直接說話。"""

NORA_MEETING_PROMPT = """你是諾拉，毒舌營養師。針對這週的身體數據，從飲食角度給出評論和下週建議。說話直接嗆辣，50字以內，繁體中文。不要在開頭說自己的名字。不要用括號描述動作，直接說話。"""

AXEL_MEETING_PROMPT = """你是艾索，賤嘴健身教練。針對這週的身體數據，從運動角度給出評論和下週目標。激將法，欠揍風格，50字以內，繁體中文。不要在開頭說自己的名字。不要用括號描述動作，直接說話。"""

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

async def get_weekly_data():
    weekly_channel = rex_bot.get_channel(WEEKLY_CHANNEL_ID)
    if weekly_channel:
        async for msg in weekly_channel.history(limit=10):
            if msg.author.bot and msg.content:
                return msg.content
    return ""

async def run_meeting(meeting_channel, weekly_data):
    history = []
    await meeting_channel.send("📊 **本週健康檢討會議開始**\n─────────────────")
    await asyncio.sleep(1)

    cole_reply = await ask_ai(COLE_MEETING_PROMPT, weekly_data, history)
    cole_channel = cole_bot.get_channel(MEETING_CHANNEL_ID)
    if cole_channel:
        await cole_channel.send(cole_reply)
    history.append({"role": "assistant", "content": f"柯爾：{cole_reply}"})
    await asyncio.sleep(2)

    nora_reply = await ask_ai(NORA_MEETING_PROMPT, weekly_data, history)
    nora_channel = nora_bot.get_channel(MEETING_CHANNEL_ID)
    if nora_channel:
        await nora_channel.send(nora_reply)
    history.append({"role": "user", "content": f"諾拉：{nora_reply}"})
    await asyncio.sleep(2)

    axel_reply = await ask_ai(AXEL_MEETING_PROMPT, weekly_data, history)
    axel_channel = axel_bot.get_channel(MEETING_CHANNEL_ID)
    if axel_channel:
        await axel_channel.send(axel_reply)
    history.append({"role": "user", "content": f"艾索：{axel_reply}"})
    await asyncio.sleep(2)

    await meeting_channel.send("─────────────────\n✅ **會議結束，下週加油！**")

@rex_bot.event
async def on_ready():
    print(f"會議室開放：{rex_bot.user}")

@rex_bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == WEEKLY_CHANNEL_ID and message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
                await asyncio.sleep(60)
                weekly_data = await get_weekly_data()
                if weekly_data:
                    meeting_channel = rex_bot.get_channel(MEETING_CHANNEL_ID)
                    if meeting_channel:
                        await run_meeting(meeting_channel, weekly_data)

    if message.content == "開會" and message.channel.id == MEETING_CHANNEL_ID:
        weekly_data = await get_weekly_data()
        if weekly_data:
            await run_meeting(message.channel, weekly_data)
        else:
            await message.channel.send("找不到本週數據，請先在每週數據頻道貼 Fitdays 截圖！")

async def main():
    await asyncio.gather(
        rex_bot.start(REX_TOKEN),
        nora_bot.start(NORA_TOKEN),
        axel_bot.start(AXEL_TOKEN),
        cole_bot.start(COLE_TOKEN),
    )

asyncio.run(main())
