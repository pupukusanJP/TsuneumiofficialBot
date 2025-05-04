import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()  # .envファイルから読み込み（ローカルテスト用）

TOKEN = os.getenv("DISCORD_TOKEN")  # Railwayに環境変数として設定する

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()  # スラッシュコマンドの同期
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="emoji", description="サーバーのすべての絵文字を表示")
async def emoji(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("このコマンドはサーバー内でのみ使用できます。", ephemeral=True)
        return

    emojis = guild.emojis
    if not emojis:
        await interaction.response.send_message("このサーバーにはカスタム絵文字がありません。", ephemeral=True)
        return

    embed = discord.Embed(title=f"{guild.name} の絵文字一覧", color=discord.Color.blue())
    emoji_list = [f"{emoji} `{emoji.name}`" for emoji in emojis]
    embed.description = "\n".join(emoji_list)

    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
