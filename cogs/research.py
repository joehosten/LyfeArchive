from pathlib import Path

import discord
import random
from discord.ext import commands

cwd = Path(__file__).parents[1]
cwd = str(cwd)
from tabulate import tabulate


class Research(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("+ Research Cog loaded")

    @commands.command(aliases=['ii', 'getinfo'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def iteminfo(self, ctx, *, item):
        item = item.replace(" ", "").lower()
        items = await self.bot.items.find("items")
        items = items["items"]
        if item not in items:
            embed = discord.Embed(title="Item Doesn't Exist", color=discord.Colour.purple())
            return await ctx.send(embed=embed)
        item = items[item]

        name, desc, emoji, value, rarity = item["name"], item["description"], item["emoji"], item["value"], item[
            "rarity"]
        embed = discord.Embed(
            title=f"{emoji} **{name}**",
            description="**Description:** `{}`\n**Rarity:** `{}`\n**Value:** $`{:,}`".format(desc, rarity, value),
            color=discord.Colour.purple()
        )
        await ctx.send(embed=embed)

    @iteminfo.error
    async def iteminfo_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Usage: `{self.bot.prefix}iteminfo (item)`")

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def find(self, ctx, *, item):
        if item == "frog" or item == "Frog":
            return await ctx.send("Searching for frogs is currently unavailable at the moment.")
        data = await self.bot.inventories.get_all()
        first, second, third, fourth, fifth = {}, {}, {}, {}, {}
        all = {}
        items = await self.bot.items.find("items")
        items = items["items"]
        item = item.replace(" ", "").lower()
        if item not in items:
            return await ctx.send(
                "That item does not exist.\n**Tip:** Items in commands generally don't contain spaces!")
        item = items[item]
        name, emoji = item["name"], item["emoji"]

        for item in data:
            for i in item["inventory"]:
                if i["name"] == name:
                    all[item["_id"]] = i["quantity"]

        all = sorted(all.items(), key=lambda k: k[1], reverse=True)
        entries = []
        count = 0
        while True:
            try:
                rand = random.choice(all)
            except IndexError:
                entries.append(["None", 0, 0])
                break
            user = self.bot.get_user(int(rand[0]))
            if user != None:
                found = False
                for i in entries:
                    if i[2] == user.id:
                        found = True
                        count -= 1

                if not found:
                    entries.append([user, rand[1], user.id])
            else:
                count -= 1
            count += 1

            if count >= len(all) or count > 4:
                break

        output = ("```" + tabulate(entries, tablefmt="simple", headers=["Player", "Amount", "User ID"]) + "```")
        embed = discord.Embed(title=f"{emoji} Owners of {name}:", description=output, color=discord.Color.gold())
        await ctx.send(embed=embed)

    @find.error
    async def find_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"Usage: `{self.bot.prefix}find (item)`")


def setup(bot):
    bot.add_cog(Research(bot))
