from pathlib import Path

import discord
import json
import motor.motor_asyncio
import os
import time
from discord.ext import commands

from utils.mongo import Document

cwd = Path(__file__).parents[0]
cwd = str(cwd)

secret_file = json.load(open(cwd + "/bot_config/secrets.json"))
prefix = secret_file["prefix"]

bot = commands.Bot(command_prefix=prefix, case_insensitive=True, owner_id=462296411141177364,
                   intents=discord.Intents.all())
bot.remove_command("help")

bot.config_token = secret_file["token"]
bot.connection_url = secret_file["mongo"]
bot.prefix = prefix
bot.blacklisted_users = []
bot.upsince = time.time()
bot.maintenancemode = False
bot.whitelisted = []
bot.lockdown = False

bot.errors = 0
bot.important_errors = 0


@bot.event
async def on_ready():
    print(f"-----\n{bot.user.name} Online\n-----\nPrefix: {bot.prefix}\n-----")
    status = secret_file["status"]
    if status == "online":
        await bot.change_presence(activity=discord.Game(name=f"{bot.prefix}help in {len(bot.guilds)} servers"))
    elif status == "idle":
        await bot.change_presence(activity=discord.Game(name=f"{bot.prefix}help in {len(bot.guilds)} servers"),
                                  status=discord.Status.idle)
    elif status == "streaming":
        await bot.change_presence(activity=discord.Streaming(name=f"{bot.prefix}help", url="https://twitch.tv/discord"))

    bot.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(bot.connection_url))
    bot.db = bot.mongo["lyfe"]
    if status == "online":
        bot.db = bot.mongo["lyfe"]
    elif status == "idle":
        bot.db = bot.mongo["lyfebeta"]
    else:
        bot.db = bot.mongo["lyfeaqua"]
    bot.inventories = Document(bot.db, "inventories")
    bot.items = Document(bot.db, "items")
    bot.trades = Document(bot.db, "trades")
    bot.playershops = Document(bot.db, "playershops")
    bot.cooldowns = Document(bot.db, "cooldowns")
    bot.welcomeback = Document(bot.db, "welcomemessage")
    bot.command_usage = Document(bot.db, "command_usage")
    print("Initialized database\n-----")


@bot.event
async def on_message(message):
    # Ignore bots
    if message.author.id == bot.user.id or message.author.bot:
        return

    ctx = await bot.get_context(message)
    if ctx.valid and not bot.lockdown:
        guild = ctx.message.guild.id
        data = await bot.welcomeback.find(guild)
        if data is None:
            welcomeback = discord.Embed(
                title="Lyfe is returning!",
                description=f"After quite a long time of inactivity, Lyfe is returning.\nPlease join our support server by doing `{bot.prefix}invite` for more info.\n**Please note, some commands may be buggy or certain features may not be available at the current time!**",
                color=discord.Color.green()
            )
            welcomeback.set_thumbnail(url=bot.user.avatar_url)
            await bot.welcomeback.upsert({"_id": ctx.message.guild.id})
            await ctx.send(embed=welcomeback)
        else:
            pass

    # Lockdown system
    if bot.lockdown and message.author.id not in json.load(open(cwd + "/bot_config/devs.json")):
        ctx = await bot.get_context(message)
        if ctx.valid:
            if message.content.lower().find("invite") != -1:
                embed = discord.Embed(title=":herb: Lyfé Invite Links",
                                      description=":mailbox_with_mail: [Invite me to other servers](https://discord.com/api/oauth2/authorize?client_id=730874220078170122&permissions=519232&scope=bot)\n<:discord:851488059975663706> [Lyfé Server](https://discord.gg/q5AYJMjqRa)",
                                      color=discord.Color.purple())
                return await ctx.send(embed=embed)
            else:
                lockdownembed = discord.Embed(
                    title="Lyfe is currently in a lockdown",
                    description=f"At the moment, commands will not work due to an error we have encountered.\nPlease join our support server by doing `{bot.prefix}invite` for more info.",
                    color=discord.Color.red()
                )
                lockdownembed.set_thumbnail(url=bot.user.avatar_url)
                return await ctx.send(embed=lockdownembed)

    # Blacklist system
    if secret_file["status"] != "idle":
        if message.author.id in bot.blacklisted_users:
            return
    else:
        if message.author.id not in bot.whitelisted:
            return

    # Auto responses go here
    if bot.user.mentioned_in(message) and message.mention_everyone is False:
        try:
            if "help" in message.content.lower() or "info" in message.content.lower():
                await message.channel.send(f"My prefix is `{bot.prefix}`")
        except discord.Forbidden:
            pass

    await bot.process_commands(message)


if __name__ == '__main__':
    for file in os.listdir(cwd + "/cogs"):
        if file.endswith(".py") and not file.startswith("_"):
            bot.load_extension(f"cogs.{file[:-3]}")

bot.run(bot.config_token, reconnect=True)
