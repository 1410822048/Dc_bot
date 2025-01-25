import os
import discord
from discord.ext import commands, tasks
from datetime import time
import asyncio

# 获取 Discord Token
TOKEN =  os.environ['DISCORD_TOKEN']

# 调试输出，确保 TOKEN 是有效的
if TOKEN is None:
    print("ERROR: DISCORD_TOKEN is not set.")
else:
    print(f"Successfully loaded token: {TOKEN[:5]}...")  # 打印前5个字符进行确认

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
            print(f"無法找到频道 ID {channel_id}，請確認頻道 ID 是否正確。")
    else:
        print("沒有找到頻道 ID，請檢查 Bot 是否已加入伺服器。")

@bot.event
async def on_message(message):
    # 檢查訊息是否來自固定成員
    if message.author.id in FIXED_USERS and message.channel.id in channel_ids:
        # 檢查訊息內容
        if message.content == "1️⃣":  # :one: 表情
            accepted_users.add(message.author.id)
            await message.channel.send(f"{message.author.mention} 已同意参加！")

            # 將用戶移動到指定的語音頻道
            voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
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

@bot.command(name="list")
async def list_accepted(ctx):
    """列出已同意参加的用户"""
    if accepted_users:
        await ctx.send(
            "已同意参加的用户：\n" +
            "\n".join([f"<@{user_id}>" for user_id in accepted_users]))
    else:
        await ctx.send("今天PASS")

# 启动机器人
if __name__ == "__main__":
    bot.run(TOKEN)