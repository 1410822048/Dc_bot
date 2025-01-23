import os
import discord
from discord.ext import commands, tasks
from datetime import time
from flask import Flask
import threading

# 获取 Discord Token
TOKEN = os.environ["DISCORD_TOKEN"]

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

# 创建 Flask 应用
app = Flask(__name__)

# 设置一个简单的首页，确保 Replit 项目在线
@app.route('/')
def index():
    return "Bot is running"

def run_flask():
    app.run(host='0.0.0.0', port=3000)

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
                    "\n\n如果想参加，請點 👍 回應！")
                await message.add_reaction("👍")
            except Exception as e:
                print(f"發送邀請訊息出錯: {e}")
        else:
            print(f"無法找到频道 ID {channel_id}，請確認頻道 ID 是否正確。")
    else:
        print("沒有找到頻道 ID，請檢查 Bot 是否已加入伺服器。")

@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.author == bot.user and reaction.emoji == "👍" and user.id in FIXED_USERS:
        accepted_users.add(user.id)
        await reaction.message.channel.send(f"{user.mention} 已同意参加！")

@bot.event
async def on_reaction_remove(reaction, user):
    if reaction.message.author == bot.user and reaction.emoji == "👍" and user.id in FIXED_USERS:
        accepted_users.discard(user.id)
        await reaction.message.channel.send(f"{user.mention} 已取消参加。")

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
    t = threading.Thread(target=run_flask)
    t.start()

# 启动机器人和 Flask 服务
if __name__ == "__main__":
    start_flask()
    bot.run(TOKEN)
