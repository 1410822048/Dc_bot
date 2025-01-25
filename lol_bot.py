import os
import discord
from discord.ext import commands, tasks
from datetime import time
import asyncio

# 獲取 Discord Token
TOKEN = os.environ['DISCORD_TOKEN']

# 啟用特權意圖
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 固定邀請的用戶 ID
FIXED_USERS = [
    542600173986250762, 627844121939279892, 394103882055417866,
    547051019473780767, 417292881028579338
]

# 存儲同意參加的用戶
accepted_users = set()

# 存儲自動獲取的頻道 ID
channel_ids = []

# 指定的語音頻道 ID
VOICE_CHANNEL_ID = 681835115994939395  # 替換為你的語音頻道 ID

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

    # 獲取所有 Bot 加入的頻道 ID
    global channel_ids
    for guild in bot.guilds:
        for channel in guild.text_channels:
            channel_ids.append(channel.id)

    if channel_ids:
        print(f"Bot 加入了以下頻道: {', '.join(map(str, channel_ids))}")
    else:
        print("Bot 未加入任何頻道。")

    # 啟動定時任務
    if not start_bot_task.is_running():
        start_bot_task.start()

# 13:00 啟動機器人
@tasks.loop(time=time(13, 15))
async def start_bot_task():
    print("機器人已啟動！")
    if not daily_invite.is_running():
        daily_invite.start()

# 14:15 關閉機器人
@tasks.loop(time=time(14, 15))
async def stop_bot_task():
    print("機器人已關閉！")
    if daily_invite.is_running():
        daily_invite.stop()
    await bot.close()

# 13:30 發送邀請訊息
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

                # 檢查同意參加的用戶數量
                if len(accepted_users) < 3:
                    await channel.send("今天PASS🫠")

                    # 將語音頻道中的所有用戶移出
                    voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
                    if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
                        for member in voice_channel.members:
                            try:
                                await member.move_to(None)  # 將用戶移出語音頻道
                                await channel.send(f"{member.mention} 已從語音頻道中移出。")
                            except discord.Forbidden:
                                await channel.send(f"沒有權限移動 {member.mention}。")
                            except discord.HTTPException as e:
                                await channel.send(f"移動用戶時出錯: {e}")
                    else:
                        await channel.send("找不到指定的語音頻道，請檢查 頻道_ID 是否正確。")
                else:
                    await channel.send("等等開幹！")

            except Exception as e:
                print(f"發送邀請訊息出錯: {e}")
        else:
            print(f"無法找到頻道 ID {channel_id}，請確認頻道 ID 是否正確。")
    else:
        print("沒有找到頻道 ID，請檢查 Bot 是否已加入伺服器。")

# 啟動機器人
if __name__ == "__main__":
    bot.run(TOKEN)