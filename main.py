import discord
from discord.ext import commands, tasks
import dotenv
import os
import asyncio
from itertools import cycle

# Load environment variables
dotenv.load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents options
intents = discord.Intents.all()
intents.message_content = True
intents.voice_states = True

# Create bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Bot status
bot_statuses = cycle(['Status 1', 'Status 2', 'Status 3'])

# Load the status inside the bot
@tasks.loop(seconds=5)
async def change_bot_status():
    await bot.change_presence(activity=discord.Game(next(bot_statuses)))

# Load the bot, first the status and then the commands
@bot.event
async def on_ready():
    print(f'{bot.user.name} is ready!')
    change_bot_status.start()

# Load cogs
async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

# Run bot
async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)

asyncio.run(main())