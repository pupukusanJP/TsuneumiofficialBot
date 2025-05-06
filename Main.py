import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# 環境変数の読み込み
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Discordのintents設定
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# Flaskを使ったkeep-alive Webサーバー
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Discord Botのイベント処理
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# おみくじコマンド
@bot.tree.command(name="omikuzi", description="おみくじを引きます")
async def omikuzi(interaction: discord.Interaction):
    fortunes = ["大吉", "中吉", "小吉", "末吉", "凶", "大凶"]
    result = random.choice(fortunes)
    await interaction.response.send_message(f"🎴 あなたの運勢は… **{result}**！")

# ラッキーカラーコマンド
@bot.tree.command(name="luckycolor", description="今日のラッキーカラーを教えます")
async def luckycolor(interaction: discord.Interaction):
    colors = ["赤", "青", "黄色", "緑", "紫", "ピンク", "白", "黒"]
    color = random.choice(colors)
    await interaction.response.send_message(f"🎨 今日のラッキーカラーは **{color}** です！")

# 起動
keep_alive()
bot.run(TOKEN)


