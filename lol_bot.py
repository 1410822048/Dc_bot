import os
import discord
from discord.ext import commands, tasks
from datetime import time
from flask import Flask
import asyncio
import threading

# 获取 Discord Token
TOKEN = os.getenv("DISCORD_TOKEN")

# 启用特权意图
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 固定邀请的用户 ID
FIXED_USERS = [
    542600173986250762, 627844121939279892, 394103882055417866,
    547051019473780767, 417292881028579338
]

# 存储同意参加的用户
accepted_users = set()

# 存储自动获取的频道 ID
channel_ids = []

# 指定的语音频道 ID
VOICE_CHANNEL_ID = 681835115994939395  # 替换为你的语音频道 ID

# 创建 Flask 应用
app = Flask(__name__)

# 设置一个简单的首页，确保 Railway 项目在线
@app.route('/')
def index():
    return "Bot is running"

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

    # 获取所有Bot加入的频道 ID
    global channel_ids
    for guild in bot.guilds:
        for channel in guild.text_channels:
            channel_ids.append(channel.id)

    if channel_ids:
        print(f"Bot 加入了以下频道: {', '.join(map(str, channel_ids))}")
    else:
        print("Bot 未加入任何频道。")

    # 启动定时任务
    if not daily_invite.is_running():
        daily_invite.start()

@tasks.loop(time=time(13, 30))
async def daily_invite():
    global channel_ids
    if channel_ids:
        channel_id = channel_ids[0]
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                accepted_users.clear()
                message = await channel.send(
                    "**單中開幹**\n"
                    "今晚要一起玩《咆嘯深淵》嗎？\n"
                    "邀請成員：\n" +
                    "\n".join([f"<@{user_id}>" for user_id in FIXED_USERS]) +
                    "\n\n如果想参加，請輸入 1️⃣；如果不想参加，請輸入 0️⃣。\n"
                    "**15 分鐘後結算**。")
                
                # 等待 15 分鐘
                await asyncio.sleep(15 * 60)  # 15 分鐘 = 900 秒

                # 检查同意参加的用户数量
                if len(accepted_users) < 3:
                    await channel.send("今天PASS🫠")

                    # 将语音频道中的所有用户移出
                    voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
                    if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
                        for member in voice_channel.members:
                            try:
                                await member.move_to(None)  # 将用户移出语音频道
                                await channel.send(f"{member.mention} 已从语音频道中移出。")
                            except discord.Forbidden:
                                await channel.send(f"没有权限移动 {member.mention}。")
                            except discord.HTTPException as e:
                                await channel.send(f"移动用户时出错: {e}")
                    else:
                        await channel.send("找不到指定的语音频道，请检查频道_ID 是否正确。")
                else:
                    await channel.send("等等开幹！")

            except Exception as e:
                print(f"发送邀请消息出错: {e}")
        else:
            print(f"无法找到频道 ID {channel_id}，请确认频道 ID 是否正确。")
    else:
        print("没有找到频道 ID，请检查 Bot 是否已加入服务器。")

@bot.event
async def on_message(message):
    # 确保其他指令（例如 !list）仍然可以正常运行
    await bot.process_commands(message)

@bot.command(name="list")
async def list_accepted(ctx):
    """列出已同意参加的用户"""
    if accepted_users:
        await ctx.send(
            "已同意参加的用户：\n" +
            "\n".join([f"<@{user_id}>" for user_id in accepted_users]))
    else:
        await ctx.send("今天PASS")

# 启动 Flask Web 服务
def start_flask():
    port = int(os.getenv("PORT", 3000))  # 使用 Railway 提供的动态端口
    app.run(host='0.0.0.0', port=port)

# 启动机器人和 Flask 服务
def start_bot():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start(TOKEN))

if __name__ == "__main__":
    # 在独立线程中启动 Flask 服务
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()

    # 启动 Discord Bot
    start_bot()
