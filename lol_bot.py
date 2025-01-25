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

# 緩存頻道對象
target_channel = None
voice_channel = None

# 指定的語音頻道 ID
VOICE_CHANNEL_ID = 681835115994939395  # 替換為你的語音頻道 ID

# 固定的邀請訊息內容
INVITE_MESSAGE = (
    "**單中開幹**\n"
    "今晚要一起玩《咆嘯深淵》嗎？\n"
    "邀請成員：\n" +
    "\n".join([f"<@{user_id}>" for user_id in FIXED_USERS]) +
    "\n\n如果想参加，請輸入 1️⃣；如果不想参加，請輸入 0️⃣。\n"
    "**15 分鐘後結算**。"
)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

    # 獲取目標頻道和語音頻道對象
    global target_channel, voice_channel
    for guild in bot.guilds:
        # 獲取第一個文字頻道
        if not target_channel:
            target_channel = guild.text_channels[0] if guild.text_channels else None
        # 獲取指定的語音頻道
        if not voice_channel:
            voice_channel = guild.get_channel(VOICE_CHANNEL_ID)

    if target_channel:
        print(f"Bot 已找到目標頻道: {target_channel.name}")
    else:
        print("Bot 未找到目標頻道。")

    if voice_channel:
        print(f"Bot 已找到語音頻道: {voice_channel.name}")
    else:
        print("Bot 未找到語音頻道。")

    # 啟動定時任務
    if not start_bot_task.is_running():
        start_bot_task.start()

# 13:15 啟動機器人
@tasks.loop(time=time(13, 15))
async def start_bot_task():
    print("機器人已啟動！")
    if not daily_invite.is_running():
        daily_invite.start()

# 14:05 關閉機器人
@tasks.loop(time=time(14, 5))
async def stop_bot_task():
    print("機器人已關閉！")
    if daily_invite.is_running():
        daily_invite.stop()
    await bot.close()

# 13:30 發送邀請訊息
@tasks.loop(time=time(13, 30))
async def daily_invite():
    if target_channel:
        try:
            accepted_users.clear()
            message = await target_channel.send(INVITE_MESSAGE)
            
            # 等待 15 分鐘
            await asyncio.sleep(15 * 60)  # 15 分鐘 = 900 秒

            # 檢查同意參加的用戶數量
            if len(accepted_users) < 3:
                await target_channel.send("今天PASS🫠")

                # 將語音頻道中的所有用戶移出
                if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
                    for member in voice_channel.members:
                        try:
                            await member.move_to(None)  # 將用戶移出語音頻道
                            await target_channel.send(f"{member.mention} 已從語音頻道中移出。")
                        except discord.Forbidden:
                            await target_channel.send(f"沒有權限移動 {member.mention}。")
                        except discord.HTTPException as e:
                            await target_channel.send(f"移動用戶時出錯: {e}")
                else:
                    await target_channel.send("找不到指定的語音頻道，請檢查 頻道_ID 是否正確。")
            else:
                await target_channel.send("等等開幹！")

        except Exception as e:
            print(f"發送邀請訊息出錯: {e}")
    else:
        print("沒有找到目標頻道，請檢查 Bot 是否已加入伺服器。")

@bot.event
async def on_message(message):
    # 檢查訊息是否來自固定成員
    if message.author.id in FIXED_USERS and message.channel.id == target_channel.id:
        # 檢查訊息內容
        if message.content == "1️⃣":  # :one: 表情
            accepted_users.add(message.author.id)
            await message.channel.send(f"{message.author.mention} 已同意参加！")

            # 將用戶移動到指定的語音頻道
            if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
                try:
                    # 檢查用戶是否在語音頻道中
                    if message.author.voice and message.author.voice.channel:
                        await message.author.move_to(voice_channel)
                        await message.channel.send(f"{message.author.mention} 已加入遊戲打屁區！")
                    else:
                        await message.channel.send(f"{message.author.mention} 請確認是否該伺服器有語音頻道。")
                except discord.Forbidden:
                    await message.channel.send(f"沒有權限移動 {message.author.mention}。")
                except discord.HTTPException as e:
                    await message.channel.send(f"移動用戶時出錯: {e}")
            else:
                await message.channel.send("找不到語音頻道，請檢查 頻道_ID 是否正確。")

        elif message.content == "0️⃣":  # :zero: 表情
            accepted_users.discard(message.author.id)
            await message.channel.send(f"{message.author.mention} 已取消参加。")

            # 將用戶從語音頻道中移出
            if message.author.voice and message.author.voice.channel:
                try:
                    await message.author.move_to(None)  # 將用戶移出語音頻道
                    await message.channel.send(f"{message.author.mention} 已從語音中移出。")
                except discord.Forbidden:
                    await message.channel.send(f"沒有權限移動 {message.author.mention}。")
                except discord.HTTPException as e:
                    await message.channel.send(f"移動用戶時出錯: {e}")

    # 確保其他指令（例如 !list）仍然可以正常運行
    await bot.process_commands(message)

# 啟動機器人
if __name__ == "__main__":
    bot.run(TOKEN)