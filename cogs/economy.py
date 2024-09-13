from pathlib import Path

import asyncio
import discord
import random
from discord.ext import commands

cwd = Path(__file__).parents[1]
cwd = str(cwd)
from tabulate import tabulate


class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("+ Economy Cog loaded")

    @commands.command(aliases=['bal'])
    async def balance(self, ctx, user=None):
        color = discord.Color.red()
        if user is None:
            user = ctx.author
            color = discord.Color.blue()
        elif len(ctx.message.mentions) == 0:
            try:
                user = self.bot.get_user(int(user))
                if user is None:
                    return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
            except ValueError:
                return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
        else:
            user = ctx.message.mentions[0]

        data = await self.bot.inventories.find(user.id)

        if data is None:
            if user != ctx.author:
                return await ctx.send("This user hasn't initialized their inventory yet.")
            else:
                return await ctx.send(
                    f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")

        balance = data["balance"]
        bankbalance = data["bankbalance"]
        banklimit = data["banklimit"]

        a = "their"
        if user == ctx.author:
            color = discord.Color.blue()
            a = "your"

        embed = discord.Embed(
            title=":moneybag: **Balance**",
            description=":dollar: **{}**'s balance is $`{:,}`\n:bank: $`{:,}`/`{:,}` is stored in {} bank".format(
                user.name, balance, bankbalance, banklimit, a),
            color=color
        )
        return await ctx.send(embed=embed)

    @commands.command(aliases=['gambling'])
    @commands.cooldown(20, 3600, commands.BucketType.user)
    async def gamble(self, ctx, game=None, amount="n"):
        data = await self.bot.inventories.find(ctx.author.id)
        if data is None:
            return await ctx.send(
                f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")

        inventory = data["inventory"]
        balance = data["balance"]
        items = await self.bot.items.find("items")
        items = items["items"]

        if game is None:
            embed = discord.Embed(title=":game_die: **Gambling**",
                                  description="Spend your money sensibly by doing some gambling!",
                                  color=discord.Color.dark_teal())
            embed.add_field(name=":package: Three Boxes",
                            value=f"Choose a prize from 3 mystery boxes! Costs $`750`\n`{self.bot.prefix}gamble boxes` or `{self.bot.prefix}threeboxes`",
                            inline=False)
            embed.add_field(name=":question: Number Guesser",
                            value=f"Guess the correct number to triple however much you enter\n`{self.bot.prefix}gamble number (amount)` or `{self.bot.prefix}numberguess`",
                            inline=False)
            embed.add_field(name="<:coin:851488568316133376> Coin Flip",
                            value=f"50% chance of doubling your money, 50% chance of losing double! You win on heads\n`{self.bot.prefix}gamble coinflip (amount)` or `{self.bot.prefix}coinflip`",
                            inline=False)
            return await ctx.send(embed=embed)

        elif game.replace(" ", "").lower() == "threeboxes" or game.replace(" ", "").lower() == "boxes" or game.replace(
                " ", "").lower() == "box":
            if balance < 750:
                return await ctx.send("Insufficient funds.")
            balance -= 750
            await ctx.send("$`750` has been taken from your account\n**Three Boxes:**")
            await ctx.send(":package: :package: :package:")
            await ctx.send("**   1^             2^            3^**\nChoose a box:")

            def check(m):
                return m.channel == ctx.channel and m.author == ctx.author

            numbers = ['1', '2', '3']
            while True:
                try:
                    message = await self.bot.wait_for('message', check=check, timeout=10)
                except asyncio.TimeoutError:
                    return await ctx.send("You ran out of time! Refunding $`750`")

                if any(ele in message.content for ele in numbers):
                    break
                else:
                    await ctx.send("Please enter 1, 2 or 3.")

            randomrarity = random.randint(1, 100)
            if 0 < randomrarity <= 60:
                randomrarity = "common"
            elif 60 < randomrarity <= 90:
                randomrarity = "uncommon"
            else:
                randomrarity = "rare"

            while True:
                item = items[random.choice(list(items))]
                if item["rarity"] == randomrarity:
                    item = item
                    break

            name, emoji = item["name"], item["emoji"]

            given = False
            for i in inventory:
                if i["name"] == name:
                    i["quantity"] += 1
                    given = True

            if not given:
                del item["emoji"], item["value"], item["description"], item["rarity"]
                item["locked"] = False
                item["quantity"] = 1
                inventory.append(item)

            embed = discord.Embed(title=":package: **Three Boxes**", description=f"You got **{emoji} {name}**!",
                                  color=discord.Color.dark_teal())
            await ctx.send(embed=embed)
            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": balance})


        elif game.replace(" ", "").lower() == "number" or game.replace(" ", "").lower() == "number guess":
            try:
                amount = int(amount)
                if amount <= 0:
                    return await ctx.send("Please enter a valid amount.")
            except Exception:
                return await ctx.send("Enter a valid amount.")

            if amount > 2500:
                return await ctx.send("The limit it $`2500`")

            if amount > balance:
                return await ctx.send(f"Insufficient funds!")

            def check(m):
                return m.channel == ctx.channel and m.author == ctx.author

            num = random.randint(1, 10)

            win = False
            for i in range(3):
                while True:
                    if i == 0:
                        embed = discord.Embed(title=":question: Number Guesser (1 to 10)",
                                              description=f"You have 3 guesses!", color=discord.Color.dark_teal())
                    else:
                        embed = discord.Embed(title=":question: Incorrect!", description=f"{3 - i} guesses remaining!",
                                              color=discord.Color.dark_teal())
                    await ctx.send(embed=embed)
                    try:
                        message = await self.bot.wait_for('message', check=check, timeout=10)
                    except asyncio.TimeoutError:
                        return await ctx.send(f"You ran out of time! Refunding $`{amount}`")

                    try:
                        input = int(message.content)
                        if 0 < input <= 10:
                            break
                        else:
                            await ctx.send("Enter a number between 1 and 10.")
                    except Exception:
                        await ctx.send("Enter a number between 1 and 10.")

                if input == num:
                    win = True
                    break

            if win:
                balance += int(amount * 1.3)
                embed = discord.Embed(title=":question: Number Guesser",
                                      description=f"**Correct!** Your earned $`{int(amount * 3)}`",
                                      color=discord.Color.dark_teal())
            else:
                balance -= amount
                embed = discord.Embed(title=":question: Number Guesser",
                                      description=f"**Incorrect!** The number was `{num}`. Your lost $`{amount}`",
                                      color=discord.Color.dark_teal())
            await ctx.send(embed=embed)
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": balance})


        elif game.replace(" ", "").lower() == "coinflip" or game.replace(" ", "").lower() == "coin" or game.replace(" ",
                                                                                                                    "").lower() == "flip":
            try:
                amount = int(amount)
                if amount <= 0:
                    return await ctx.send("Please enter a valid amount.")
            except Exception:
                return await ctx.send(f"Usage: `{self.bot.prefix}gamble coinflip (amount)`")

            if amount > 10000:
                return await ctx.send("The limit it $`10000`")

            if balance < amount:
                return await ctx.send(f"Insufficient funds!")

            balance - amount

            embed = discord.Embed(title=f"<:coin:851488568316133376> You have bet $`{int(amount)}`",
                                  description=f"Flipping coin <a:loading:851488071567933440>",
                                  color=discord.Color.dark_teal())
            message = await ctx.send(embed=embed)
            await asyncio.sleep(2)
            coin = ['heads', 'tails']
            coin = random.choice(coin)
            if coin == 'heads':
                balance += amount
                embed = discord.Embed(title=f"<:coin:851488568316133376> You have bet $`{int(amount)}`",
                                      description=f"Coin has been flipped! It's **heads**, you win! You gained $`{amount}`",
                                      color=discord.Color.dark_teal())
            else:
                balance -= amount
                embed = discord.Embed(title=f"<:coin:851488568316133376> You have bet $`{int(amount)}`",
                                      description=f"Coin has been flipped! It's **tails**, you lose! You lost $`{amount}`",
                                      color=discord.Color.dark_teal())
            await message.edit(embed=embed)
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": balance})

    ########################################
    ##### Standalone gambling commands #####
    ########################################

    # Threeboxes
    @commands.command()
    @commands.cooldown(20, 3600, commands.BucketType.user)
    async def threeboxes(self, ctx):
        data = await self.bot.inventories.find(ctx.author.id)
        if data is None:
            return await ctx.send(
                f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")

        inventory = data["inventory"]
        balance = data["balance"]
        items = await self.bot.items.find("items")
        items = items["items"]
        if balance < 750:
            return await ctx.send("Insufficient funds.")
        balance -= 750
        await ctx.send("$`750` has been taken from your account\n**Three Boxes:**")
        await ctx.send(":package: :package: :package:")
        await ctx.send("**   1^             2^            3^**\nChoose a box:")

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        numbers = ['1', '2', '3']
        while True:
            try:
                message = await self.bot.wait_for('message', check=check, timeout=10)
            except asyncio.TimeoutError:
                return await ctx.send("You ran out of time! Refunding $`750`")

            if any(ele in message.content for ele in numbers):
                break
            else:
                await ctx.send("Please enter 1, 2 or 3.")

        randomrarity = random.randint(1, 100)
        if 0 < randomrarity <= 60:
            randomrarity = "common"
        elif 60 < randomrarity <= 90:
            randomrarity = "uncommon"
        else:
            randomrarity = "rare"

        while True:
            item = items[random.choice(list(items))]
            if item["rarity"] == randomrarity:
                item = item
                break

        name, emoji = item["name"], item["emoji"]

        given = False
        for i in inventory:
            if i["name"] == name:
                i["quantity"] += 1
                given = True

        if not given:
            del item["emoji"], item["value"], item["description"], item["rarity"]
            item["locked"] = False
            item["quantity"] = 1
            inventory.append(item)

        embed = discord.Embed(title=":package: **Three Boxes**", description=f"You got **{emoji} {name}**!",
                              color=discord.Color.dark_teal())
        await ctx.send(embed=embed)
        await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
        await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": balance})
        return

    # Number guess
    @commands.command()
    @commands.cooldown(20, 3600, commands.BucketType.user)
    async def numberguess(self, ctx, amount):
        data = await self.bot.inventories.find(ctx.author.id)
        if data is None:
            return await ctx.send(
                f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")

        balance = data["balance"]
        try:
            amount = int(amount)
            if amount <= 0:
                return await ctx.send("Please enter a valid amount.")
        except Exception:
            return await ctx.send("Enter a valid amount.")

        if amount > 2500:
            return await ctx.send("The limit it $`2500`")

        if amount > balance:
            return await ctx.send(f"Insufficient funds!")

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        num = random.randint(1, 10)

        win = False
        for i in range(3):
            while True:
                if i == 0:
                    embed = discord.Embed(title=":question: Number Guesser (1 to 10)",
                                          description=f"You have 3 guesses!", color=discord.Color.dark_teal())
                else:
                    embed = discord.Embed(title=":question: Incorrect!", description=f"{3 - i} guesses remaining!",
                                          color=discord.Color.dark_teal())
                await ctx.send(embed=embed)
                try:
                    message = await self.bot.wait_for('message', check=check, timeout=10)
                except asyncio.TimeoutError:
                    return await ctx.send(f"You ran out of time! Refunding $`{amount}`")

                try:
                    input = int(message.content)
                    if 0 < input <= 10:
                        break
                    else:
                        await ctx.send("Enter a number between 1 and 10.")
                except Exception:
                    await ctx.send("Enter a number between 1 and 10.")

            if input == num:
                win = True
                break

        if win:
            balance += int(amount * 1.3)
            embed = discord.Embed(title=":question: Number Guesser",
                                  description=f"**Correct!** Your earned $`{int(amount * 3)}`",
                                  color=discord.Color.dark_teal())
        else:
            balance -= amount
            embed = discord.Embed(title=":question: Number Guesser",
                                  description=f"**Incorrect!** The number was `{num}`. Your lost $`{amount}`",
                                  color=discord.Color.dark_teal())
        await ctx.send(embed=embed)
        await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": balance})
        return

    # Coinflip
    @commands.command(aliases=["cf"])
    @commands.cooldown(20, 3600, commands.BucketType.user)
    async def coinflip(self, ctx, amount):
        data = await self.bot.inventories.find(ctx.author.id)
        if data is None:
            return await ctx.send(
                f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")

        balance = data["balance"]
        items = await self.bot.items.find("items")
        try:
            amount = int(amount)
            if amount <= 0:
                return await ctx.send("Please enter a valid amount.")
        except Exception:
            return await ctx.send(f"Usage: `{self.bot.prefix}gamble coinflip (amount)`")

        if amount > 10000:
            return await ctx.send("The limit it $`10000`")

        if balance < amount:
            return await ctx.send(f"Insufficient funds!")

        balance - amount

        embed = discord.Embed(title=f"<:coin:851488568316133376> You have bet $`{int(amount)}`",
                              description=f"Flipping coin <a:loading:851488071567933440>",
                              color=discord.Color.dark_teal())
        message = await ctx.send(embed=embed)
        await asyncio.sleep(2)
        coin = ['heads', 'tails']
        coin = random.choice(coin)
        if coin == 'heads':
            balance += amount
            embed = discord.Embed(title=f"<:coin:851488568316133376> You have bet $`{int(amount)}`",
                                  description=f"Coin has been flipped! It's **heads**, you win! You gained $`{amount}`",
                                  color=discord.Color.dark_teal())
        else:
            balance -= amount
            embed = discord.Embed(title=f"<:coin:851488568316133376> You have bet $`{int(amount)}`",
                                  description=f"Coin has been flipped! It's **tails**, you lose! You lost $`{amount}`",
                                  color=discord.Color.dark_teal())
        await message.edit(embed=embed)
        await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": balance})
        return

    @commands.command()
    async def shop(self, ctx):
        entries = [
            ["Sponge", "$10", f"{self.bot.prefix}buy sponge"],
            ["Frog", "$250", f"{self.bot.prefix}buy frog"],
            ["ID", "$500", f"{self.bot.prefix}buy id"],
            ["Crystal", "$500", f"{self.bot.prefix}buy crystal"],
            ["Key", "$500", f"{self.bot.prefix}buy key"],
            ["Dynamite", "$1,000", f"{self.bot.prefix}buy dynamite"],
            ["Hammer", "$1,500", f"{self.bot.prefix}buy hammer"],
            ["Lock", "$2,000", f"{self.bot.prefix}buy lock"]
        ]

        output = ("The place to buy useful items\n```" + tabulate(entries, tablefmt="simple",
                                                                  headers=["Item", "Cost", "Command"]) + "```")
        embed = discord.Embed(title=":shopping_cart: Item Shop:", description=output, color=discord.Color.gold())
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def buy(self, ctx, item, quantity="1"):
        data = await self.bot.inventories.find(ctx.author.id)
        if data is None:
            return await ctx.send(
                f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return await ctx.send(
                    "Please enter a valid quantity.\n**Tip:** Items in commands generally don't contain spaces!")
        except Exception:
            return await ctx.send(
                "Please enter a valid quantity.\n**Tip:** Items in commands generally don't contain spaces!")

        inventory = data["inventory"]
        bal = data["balance"]
        item = item.replace(" ", "").lower()
        items = await self.bot.items.find("items")
        items = items["items"]

        # ITEMS
        if item == "sponge":
            item = items["sponge"]
            name, emoji, cost = item["name"], item["emoji"], item["value"]

            cost = int(cost * quantity)

            if bal < cost:
                return await ctx.send(
                    f"$`{cost}` is required to purchase this. You only have $`{bal}` and need another $`{cost - bal}` to afford this.")

            bal -= cost

            for i in range(quantity):
                given = False
                for i in inventory:
                    if i["name"] == name:
                        i["quantity"] += 1
                        given = True

                if not given:
                    del item["emoji"], item["value"], item["description"], item["rarity"]
                    item["locked"] = False
                    item["quantity"] = 1
                    inventory.append(item)

            embed = discord.Embed(title=f"Purchase Successful",
                                  description=f"Purchased: {emoji} **{name}**\nQuantity: `{quantity}`\nMoney spent: $`{cost}`\nNew balance: $`{bal}`",
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)
            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})

        elif item == "id" or item == "idcard":
            item = items["id"]
            name, emoji, cost = item["name"], item["emoji"], item["value"]

            cost = int(cost * quantity)

            if bal < cost:
                return await ctx.send(
                    f"$`{cost}` is required to purchase this. You only have $`{bal}` and need another $`{cost - bal}` to afford this.")

            bal -= cost

            for i in range(quantity):
                given = False
                for i in inventory:
                    if i["name"] == name:
                        i["quantity"] += 1
                        given = True

                if not given:
                    del item["emoji"], item["value"], item["description"], item["rarity"]
                    item["locked"] = False
                    item["quantity"] = 1
                    inventory.append(item)

            embed = discord.Embed(title=f"Purchase Successful",
                                  description=f"Purchased: {emoji} **{name}**\nQuantity: `{quantity}`\nMoney spent: $`{cost}`\nNew balance: $`{bal}`",
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)
            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})

        elif item == "frog":
            item = items["frog"]
            name, emoji, cost = item["name"], item["emoji"], item["value"]

            cost = int(cost * quantity)

            if bal < cost:
                return await ctx.send(
                    f"$`{cost}` is required to purchase this. You only have $`{bal}` and need another $`{cost - bal}` to afford this.")

            bal -= cost

            for i in range(quantity):
                given = False
                for i in inventory:
                    if i["name"] == name:
                        i["quantity"] += 1
                        given = True

                if not given:
                    del item["emoji"], item["value"], item["description"], item["rarity"]
                    item["locked"] = False
                    item["quantity"] = 1
                    inventory.append(item)

            embed = discord.Embed(title=f"Purchase Successful",
                                  description=f"Purchased: {emoji} **{name}**\nQuantity: `{quantity}`\nMoney spent: $`{cost}`\nNew balance: $`{bal}`",
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)
            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})

        elif item == "crystal" or item == "gem":
            item = items["crystal"]
            name, emoji, cost = item["name"], item["emoji"], item["value"]

            cost = int(cost * quantity)

            if bal < cost:
                return await ctx.send(
                    f"$`{cost}` is required to purchase this. You only have $`{bal}` and need another $`{cost - bal}` to afford this.")

            bal -= cost

            for i in range(quantity):
                given = False
                for i in inventory:
                    if i["name"] == name:
                        i["quantity"] += 1
                        given = True

                if not given:
                    del item["emoji"], item["value"], item["description"], item["rarity"]
                    item["locked"] = False
                    item["quantity"] = 1
                    inventory.append(item)

            embed = discord.Embed(title=f"Purchase Successful",
                                  description=f"Purchased: {emoji} **{name}**\nQuantity: `{quantity}`\nMoney spent: $`{cost}`\nNew balance: $`{bal}`",
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)
            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})

        elif item == "key" or item == "Key":
            item = items["key"]
            name, emoji, cost = item["name"], item["emoji"], item["value"]

            cost = int(cost * quantity)

            if bal < cost:
                return await ctx.send(
                    f"$`{cost}` is required to purchase this. You only have $`{bal}` and need another $`{cost - bal}` to afford this.")

            bal -= cost

            for i in range(quantity):
                given = False
                for i in inventory:
                    if i["name"] == name:
                        i["quantity"] += 1
                        given = True

                if not given:
                    del item["emoji"], item["value"], item["description"], item["rarity"]
                    item["locked"] = False
                    item["quantity"] = 1
                    inventory.append(item)

            embed = discord.Embed(title=f"Purchase Successful",
                                  description=f"Purchased: {emoji} **{name}**\nQuantity: `{quantity}`\nMoney spent: $`{cost}`\nNew balance: $`{bal}`",
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)
            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})

        elif item == "boomstick" or item == "dynamite":
            item = items["dynamite"]
            name, emoji, cost = item["name"], item["emoji"], item["value"]

            cost = int(cost * quantity)

            if bal < cost:
                return await ctx.send(
                    f"$`{cost}` is required to purchase this. You only have $`{bal}` and need another $`{cost - bal}` to afford this.")

            bal -= cost

            for i in range(quantity):
                given = False
                for i in inventory:
                    if i["name"] == name:
                        i["quantity"] += 1
                        given = True

                if not given:
                    del item["emoji"], item["value"], item["description"], item["rarity"]
                    item["locked"] = False
                    item["quantity"] = 1
                    inventory.append(item)

            embed = discord.Embed(title=f"Purchase Successful",
                                  description=f"Purchased: {emoji} **{name}**\nQuantity: `{quantity}`\nMoney spent: $`{cost}`\nNew balance: $`{bal}`",
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)
            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})

        elif item == "hammer" or item == "sledgehammer":
            item = items["hammer"]
            name, emoji, cost = item["name"], item["emoji"], item["value"]

            cost = int(cost * quantity)

            if bal < cost:
                return await ctx.send(
                    f"$`{cost}` is required to purchase this. You only have $`{bal}` and need another $`{cost - bal}` to afford this.")

            bal -= cost

            for i in range(quantity):
                given = False
                for i in inventory:
                    if i["name"] == name:
                        i["quantity"] += 1
                        given = True

                if not given:
                    del item["emoji"], item["value"], item["description"], item["rarity"]
                    item["locked"] = False
                    item["quantity"] = 1
                    inventory.append(item)

            embed = discord.Embed(title=f"Purchase Successful",
                                  description=f"Purchased: {emoji} **{name}**\nQuantity: `{quantity}`\nMoney spent: $`{cost}`\nNew balance: $`{bal}`",
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)
            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})

        elif item == "lock" or item == "Lock":
            item = items["lock"]
            name, emoji, cost = item["name"], item["emoji"], item["value"]

            cost = int(cost * quantity)

            if bal < cost:
                return await ctx.send(
                    f"$`{cost}` is required to purchase this. You only have $`{bal}` and need another $`{cost - bal}` to afford this.")

            bal -= cost

            for i in range(quantity):
                given = False
                for i in inventory:
                    if i["name"] == name:
                        i["quantity"] += 1
                        given = True

                if not given:
                    del item["emoji"], item["value"], item["description"], item["rarity"]
                    item["locked"] = False
                    item["quantity"] = 1
                    inventory.append(item)

            embed = discord.Embed(title=f"Purchase Successful",
                                  description=f"Purchased: {emoji} **{name}**\nQuantity: `{quantity}`\nMoney spent: $`{cost}`\nNew balance: $`{bal}`",
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)
            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})

        else:
            await ctx.send("I couldn't find that item in the shop.")

    @buy.error
    async def buy_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Usage: `{self.bot.prefix}buy (item) [quantity]`")

    @commands.command()
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def sell(self, ctx, item, quantity="1"):
        data = await self.bot.inventories.find(ctx.author.id)
        if data is None:
            return await ctx.send(
                f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return await ctx.send(
                    "Please enter a valid quantity.\n**Tip:** Items in commands generally don't contain spaces!")
        except Exception:
            return await ctx.send(
                "Please enter a valid quantity.\n**Tip:** Items in commands generally don't contain spaces!")

        item = item.replace(" ", "").lower()
        items = await self.bot.items.find("items")
        items = items["items"]
        if item not in items:
            return await ctx.send("That item does not exist.")

        inventory = data["inventory"]
        item = items[item.lower()]
        name, emoji = item["name"], item["emoji"]

        change = False
        for i in inventory:
            if i["name"] == name:
                if i["quantity"] < quantity:
                    return await ctx.send(f"You don't have that many **{emoji} {name}s**")

                if i["locked"]:
                    return await ctx.send(f"**{emoji} {name}** is locked in your inventory.")

                if i["quantity"] == 1:
                    inventory.remove(i)
                    change = True
                else:
                    i["quantity"] -= quantity
                    if i["quantity"] == 0:
                        inventory.remove(i)
                    change = True

        if not change:
            return await ctx.send(f"You don't have a **{emoji} {name}**.")

        value = item["value"]
        balance = data["balance"]
        value = int(value * 0.75)
        balance += int(value * quantity)
        if quantity == 1:
            await ctx.send(f"You sold **{emoji} {name}** for $`{value}`. Your balance is now $`{balance}`.")
        else:
            await ctx.send(
                f"You sold **{quantity} {emoji} {name}s** for $`{value}` each. Your balance is now $`{balance}`.")
        await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
        await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": balance})

    @sell.error
    async def sell_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Usage: `{self.bot.prefix}sell (item) [quantity]`")

    @commands.command(aliases=['donate'])
    async def give(self, ctx, user, item, quantity="1"):
        if len(ctx.message.mentions) == 0:
            try:
                user = self.bot.get_user(int(user))
                if user is None:
                    return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
            except ValueError:
                return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
        else:
            user = ctx.message.mentions[0]

        mydata = await self.bot.inventories.find(ctx.author.id)
        if mydata is None:
            return await ctx.send(
                f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")
        myinventory = mydata["inventory"]

        items = await self.bot.items.find("items")
        items = items["items"]

        yourdata = await self.bot.inventories.find(user.id)
        if yourdata is None:
            return await ctx.send("This user hasn't initialized their inventory yet.")
        yourinventory = yourdata["inventory"]

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return await ctx.send(
                    "Please enter a valid quantity.\n**Tip:** Items in commands generally don't contain spaces!")
        except Exception:
            return await ctx.send(
                "Please enter a valid quantity.\n**Tip:** Items in commands generally don't contain spaces!")

        if user.id == ctx.author.id:
            return await ctx.send("That's pointless.")

        if item.lower() not in items:
            return await ctx.send("That item does not exist.")
        item = items[item.lower()]
        name, emoji = item["name"], item["emoji"]

        change = False
        for i in myinventory:
            if i["name"] == name:
                if i["quantity"] < quantity:
                    return await ctx.send(f"You don't have that many **{emoji} {name}s**")

                if i["locked"]:
                    return await ctx.send(f"**{emoji} {name}** is locked in your inventory.")

                if i["quantity"] == 1:
                    myinventory.remove(i)
                    change = True
                else:
                    i["quantity"] -= quantity
                    if i["quantity"] == 0:
                        myinventory.remove(i)
                    change = True

        if not change:
            return await ctx.send(f"You don't have a **{emoji} {name}**.")

        given = False
        for i in yourinventory:
            if i["name"] == name:
                i["quantity"] += quantity
                given = True

        if not given:
            del item["emoji"], item["value"], item["description"], item["rarity"]
            item["locked"] = False
            item["quantity"] = quantity
            yourinventory.append(item)

        if quantity == 1:
            await ctx.send(f"**{emoji} {name}** transferred from **{ctx.author.name}** to **{user.name}**.")
        else:
            await ctx.send(f"**{quantity} {emoji} {name}s** transferred from **{ctx.author.name}** to **{user.name}**.")
        await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": myinventory})
        await self.bot.inventories.upsert({"_id": user.id, "inventory": yourinventory})

    @give.error
    async def give_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"Usage: `{self.bot.prefix}give (user) (item) [quantity]`")

    @commands.command()
    async def pay(self, ctx, user, amount=None):
        if len(ctx.message.mentions) == 0:
            try:
                user = self.bot.get_user(int(user))
                if user is None:
                    return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
            except ValueError:
                return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
        else:
            user = ctx.message.mentions[0]

        if user == ctx.author:
            return await ctx.send("That's pointless.")

        try:
            amount = int(amount)
            if amount <= 0:
                return await ctx.send(
                    "Please enter a valid quantity.\n**Tip:** Items in commands generally don't contain spaces!")
        except Exception:
            return await ctx.send(f"Enter a valid amount. Usage: `{self.bot.prefix}pay (user) (amount)`")

        author_data = await self.bot.inventories.find(ctx.author.id)
        if author_data is None:
            return await ctx.send(
                f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")
        author_balance = int(author_data["balance"])
        if amount > author_balance:
            return await ctx.send(f"Insufficient funds, you only have $`{author_balance}`")

        user_data = await self.bot.inventories.find(user.id)
        if user_data is None:
            return await ctx.send(f"**{user.name}** hasn't initialized their inventory yet.")
        user_balance = int(user_data["balance"])

        author_balance -= amount
        user_balance += amount
        await ctx.send(f"Paid **{user.name}** $`{amount}`")
        await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": author_balance})
        await self.bot.inventories.upsert({"_id": user.id, "balance": user_balance})

    @pay.error
    async def pay_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"Usage: `{self.bot.prefix}pay (user) (amount)`")

    @commands.command(aliases=['playershops', 'pshops', 'playershop'])
    async def pshop(self, ctx, argument=None, item=None, cq=None, cq2=None):
        entries = []

        # ADD

        if argument == "add":
            if item is None or cq is None:
                return await ctx.send(f"Usage: `{self.bot.prefix}pshop add (item) (cost) [quantity]`")

            data = await self.bot.inventories.find(ctx.author.id)
            items = await self.bot.items.find("items")
            items = items["items"]

            if item.lower() not in items:
                return await ctx.send("That item does not exist.")

            item = items[item.lower()]
            name, emoji = item["name"], item["emoji"]

            try:
                if cq2 is None:
                    cq2 = 1
                quantity = int(cq2)
                if quantity <= 0:
                    return await ctx.send(
                        "Please enter a valid quantity.\n**Tip:** Items in commands generally don't contain spaces!")
                if quantity > 15000:
                    return await ctx.send("The limit is $`15000`")
            except Exception:
                return await ctx.send(
                    "Please enter a valid quantity.\n**Tip:** Items in commands generally don't contain spaces!")

            inventory = data["inventory"]
            found = False
            for i in inventory:
                if i["name"] == name:
                    if i["locked"] is True:
                        return await ctx.send(f"{emoji} **{name}** is locked in your inventory.")
                    if i["quantity"] < quantity:
                        return await ctx.send(f"You don't have that many {emoji} **{name}s**.")
                    i["quantity"] -= quantity
                    if i["quantity"] == 0:
                        inventory.remove(i)
                    found = True
            if not found:
                return await ctx.send(f"You don't have {emoji} **{name}** in your inventory.")

            try:
                price = int(cq)
            except Exception:
                return await ctx.send(
                    "Please enter a valid price.\n**Tip:** Items in commands generally don't contain spaces!")

            data = await self.bot.playershops.find(ctx.author.id)
            if data is None:
                shop = []
            else:
                shop = data["shop"]
                for i in shop:
                    if i["item"] == name.replace(" ", "").lower():
                        return await ctx.send("You already have that listed in your shop.")

            shop.append({"item": name.replace(" ", "").lower(), "price": price, "stock": quantity})
            await self.bot.playershops.upsert({"_id": ctx.author.id, "shop": shop})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})
            await ctx.send("Added **{:,} **x** {} {}**  to your shop.".format(quantity, emoji, name))

        # REMOVE

        elif argument == "remove":
            if item is None:
                return await ctx.send(f"Usage: `{self.bot.prefix}pshop remove (item)`")

            items = await self.bot.items.find("items")
            items = items["items"]

            if item.lower() not in items:
                return await ctx.send("That item does not exist.")

            item = items[item.lower()]
            name, emoji = item["name"], item["emoji"]

            data = await self.bot.playershops.find(ctx.author.id)
            if data is None:
                return await ctx.send("You don't have a shop.")

            shop = data["shop"]
            found = False
            for i in shop:
                if i["item"] == name.replace(" ", "").lower():
                    quantity = i["stock"]
                    shop.remove(i)
                    found = True
            if not found:
                return await ctx.send(f"You aren't selling {emoji} **{name}**")

            player_data = await self.bot.inventories.find(ctx.author.id)
            inventory = player_data["inventory"]

            found = False
            for i in inventory:
                if i["name"] == name:
                    i["quantity"] += quantity
                    found = True

            if not found:
                del item["emoji"], item["value"], item["description"], item["rarity"]
                item["locked"] = False
                item["quantity"] = quantity
                inventory.append(item)

            await ctx.send("Removed **{:,} **x** {} {}** from your shop.".format(quantity, emoji, name))
            if len(shop) == 0:
                await self.bot.playershops.delete(ctx.author.id)
            else:
                await self.bot.playershops.upsert({"_id": ctx.author.id, "shop": shop})

            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": inventory})


        # BUY

        elif argument == "buy":  # ,pshop buy 1231231 shoppingcart 1
            if item is None or cq is None:
                return await ctx.send(f"Usage: `{self.bot.prefix}pshop buy (user) (item) [quantity]`")

            user = item
            if len(ctx.message.mentions) == 0:
                try:
                    if self.bot.get_user(int(user)) == None:
                        return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
                    else:
                        user = self.bot.get_user(int(user))
                except ValueError:
                    return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
            else:
                user = ctx.message.mentions[0]

            user_shop_data = await self.bot.playershops.find(user.id)
            if user_shop_data is None:
                return await ctx.send("This user doesn't have a shop.")

            if user == ctx.author:
                return await ctx.send("That's pointless.")

            shop = user_shop_data["shop"]

            item = cq
            try:
                if cq2 is None:
                    cq2 = 1
                quantity = int(cq2)
            except Exception:
                return await ctx.send(
                    "Please enter a valid quantity.\n**Tip:** Items in commands generally don't contain spaces!")

            item = item.replace(" ", "").lower()
            items = await self.bot.items.find("items")
            items = items["items"]
            if item not in items:
                return await ctx.send("That item does not exist.")
            item = items[item]
            name, emoji = item["name"], item["emoji"]

            raw_name = item["name"].replace(" ", "").lower()

            found = False
            for i in shop:
                if i["item"] == raw_name:
                    price = i["price"]
                    stock = i["stock"]
                    found = True
            if not found:
                return await ctx.send(f"**{user}** is not selling a {emoji} **{name}")

            user_data = await self.bot.inventories.find(user.id)
            user_inventory = user_data["inventory"]
            user_balance = user_data["balance"]

            if quantity > stock:
                return await ctx.send(f"That quantity is too great. There aren't that many for sale.")

            author_data = await self.bot.inventories.find(ctx.author.id)
            if author_data is None:
                return await ctx.send(
                    "I'm suprised you made it this far without initializing your inventory. Go do that though.")
            author_inventory = author_data["inventory"]
            author_balance = author_data["balance"]
            if author_balance < price * quantity:
                return await ctx.send(
                    "$`{:,}` is required to purchase this. You only have $`{:,}` and need another $`{:,}` to afford this.".format(
                        price * quantity, author_balance, price * quantity - author_balance))

            # Set balances
            author_balance -= int(price * quantity)
            user_balance += int(price * quantity)

            # Set buyer's inventory
            given = False
            for i in author_inventory:
                if i["name"] == name:
                    i["quantity"] += 1
                    given = True

            if not given:
                del item["emoji"], item["value"], item["description"], item["rarity"]
                item["locked"] = False
                item["quantity"] = 1
                author_inventory.append(item)

            # Change shop
            for i in shop:
                if i["item"] == raw_name:
                    i["stock"] -= quantity
                    if i["stock"] == 0:
                        shop.remove(i)

            embed = discord.Embed(title=f"Purchase Successful",
                                  description="Purchased: {} **{}**\nQuantity: `{:,}`\nMoney spent: $`{:,}`\nNew balance: $`{:,}`".format(
                                      emoji, name, quantity, price * quantity, author_balance),
                                  color=discord.Color.gold())
            await self.bot.inventories.upsert({"_id": ctx.author.id, "inventory": author_inventory})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": author_balance})
            await self.bot.inventories.upsert({"_id": user.id, "balance": user_balance})
            if len(shop) == 0:
                await self.bot.playershops.delete(user.id)
            else:
                await self.bot.playershops.upsert({"_id": user.id, "shop": shop})
            await ctx.send(embed=embed)

            embed = discord.Embed(title=f"**{ctx.author}** bought from your shop!",
                                  description="Purchased: {} **{}**\nQuantity: `{:,}`\nMoney gained: $`{:,}`".format(
                                      emoji, name, quantity, price * quantity), color=discord.Color.gold())
            embed.set_footer(text=f"ID: {ctx.author.id}")
            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                pass

        # SPECIFIC

        elif argument == "show" or argument == "view":
            if item is None:
                user = ctx.author
            elif len(ctx.message.mentions) == 0:
                try:
                    if self.bot.get_user(int(item)) == None:
                        return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
                    else:
                        user = self.bot.get_user(int(item))
                except ValueError:
                    return await ctx.send("I couldn't find that user.\n**Tip:** Mention them or use their id.")
            else:
                user = ctx.message.mentions[0]

            data = await self.bot.inventories.find(user.id)
            inventory = data["inventory"]

            data = await self.bot.playershops.find(user.id)
            if data is None:
                return await ctx.send("This user doesn't have a shop.")

            items = await self.bot.items.find("items")
            items = items["items"]

            shop = data["shop"]
            for i in shop:
                entries.append([items[i["item"]]["name"], f'${i["price"]}', i["stock"]])

            if entries == []:
                entries.append(["OUT", "OF", "STOCK"])

            output = ("```" + tabulate(entries, tablefmt="simple", headers=["Item", "Price", "Stock"]) + "```")
            embed = discord.Embed(title=f":shopping_cart: **{user.name}'s** Shop", description=output,
                                  color=discord.Color.gold())
            await ctx.send(embed=embed)


        # SHOW ALL

        else:
            shops = await self.bot.playershops.get_all()
            if shops == []:
                entries.append(["None", 0, 0])
                output = ("```" + tabulate(entries, tablefmt="simple", headers=["Player", "Items", "User ID"]) + "```")
                embed = discord.Embed(title=f":shopping_cart: Player Shops:", description=output,
                                      color=discord.Color.gold())
                return await ctx.send(embed=embed)
            else:
                for i in shops:
                    id = i["_id"]
                    user = self.bot.get_user(id)
                    if user is None:
                        return ctx.send("Finding the user failed.")
                    stock = len(i["shop"])
                    entries.append([user, stock, int(id)])

                output = ("```" + tabulate(entries, tablefmt="simple", headers=["Player", "Items", "User ID"]) + "```")
                embed = discord.Embed(title=f":shopping_cart: Player Shops:", description=output,
                                      color=discord.Color.gold())
                return await ctx.send(embed=embed)

    @commands.command(aliases=['bank'])
    async def banks(self, ctx, *, item="n"):
        data = await self.bot.inventories.find(ctx.author.id)
        if data is None:
            return await ctx.send(
                f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")

        price = {"small": 1250, "medium": 2500, "large": 5000, "massive": 10000}
        stores = {"small": 2500, "medium": 7500, "large": 20000, "massive": 50000}

        inventory = data["inventory"]
        bal = data["balance"]
        banklimit = data["banklimit"]

        item = item.replace(" ", "").lower()
        if item == "smallbankslot" or item == "smallbank":
            cost = price["small"]

            if bal < cost:
                return await ctx.send(
                    "$`{:,}` is required to purchase this. You only have $`{:,}` and need another $`{:,}` to afford this.".format(
                        cost, bal, cost - bal))

            bal -= cost
            banklimit += stores["small"]
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "banklimit": banklimit})
            embed = discord.Embed(title=f"Purchase Successful",
                                  description="Purchased: :bank: **Small Bank Slot**\nMoney spent: $`{:,}`\nNew balance: $`{:,}`".format(
                                      cost, bal), color=discord.Color.gold())
            await ctx.send(embed=embed)

        elif item == "mediumbankslot" or item == "mediumbank":
            cost = price["medium"]

            if bal < cost:
                return await ctx.send(
                    "$`{:,}` is required to purchase this. You only have $`{:,}` and need another $`{:,}` to afford this.".format(
                        cost, bal, cost - bal))

            bal -= cost
            banklimit += stores["medium"]
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "banklimit": banklimit})
            embed = discord.Embed(title=f"Purchase Successful",
                                  description="Purchased: :bank: **Medium Bank Slot**\nMoney spent: $`{:,}`\nNew balance: $`{:,}`".format(
                                      cost, bal), color=discord.Color.gold())
            await ctx.send(embed=embed)

        elif item == "largebankslot" or item == "largebank":
            cost = price["large"]

            if bal < cost:
                return await ctx.send(
                    "$`{:,}` is required to purchase this. You only have $`{:,}` and need another $`{:,}` to afford this.".format(
                        cost, bal, cost - bal))

            bal -= cost
            banklimit += stores["large"]
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "banklimit": banklimit})
            embed = discord.Embed(title=f"Purchase Successful",
                                  description="Purchased: :bank: **Large Bank Slot**\nMoney spent: $`{:,}`\nNew balance: $`{:,}`".format(
                                      cost, bal), color=discord.Color.gold())
            await ctx.send(embed=embed)

        elif item == "massivebankslot" or item == "massivebank":
            cost = price["massive"]

            if bal < cost:
                return await ctx.send(
                    "$`{:,}` is required to purchase this. You only have $`{:,}` and need another $`{:,}` to afford this.".format(
                        cost, bal, cost - bal))

            bal -= cost
            banklimit += stores["massive"]
            await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": bal})
            await self.bot.inventories.upsert({"_id": ctx.author.id, "banklimit": banklimit})
            embed = discord.Embed(title=f"Purchase Successful",
                                  description="Purchased: :bank: **Massive Bank Slot**\nMoney spent: $`{:,}`\nNew balance: $`{:,}`".format(
                                      cost, bal), color=discord.Color.gold())
            await ctx.send(embed=embed)

        else:
            entries = [
                ["Small Bank Slot", "${:,}".format(price["small"]), "${:,}".format(stores["small"]),
                 f"{self.bot.prefix}bank smallbank"],
                ["Medium Bank Slot", "${:,}".format(price["medium"]), "${:,}".format(stores["medium"]),
                 f"{self.bot.prefix}bank mediumbank"],
                ["Large Bank Slot", "${:,}".format(price["large"]), "${:,}".format(stores["large"]),
                 f"{self.bot.prefix}bank largebank"],
                ["Massive Bank Slot", "${:,}".format(price["massive"]), "${:,}".format(stores["massive"]),
                 f"{self.bot.prefix}bank massivebank"]
            ]

            output = ("Protect your money from thieves\n```" + tabulate(entries, tablefmt="simple",
                                                                        headers=["Item", "Cost", "Stores",
                                                                                 "Command"]) + "```")
            embed = discord.Embed(title=":bank: Banks:", description=output, color=discord.Color.gold())
            await ctx.send(embed=embed)

    @commands.command(aliases=['dep'])
    async def deposit(self, ctx, amount="null"):
        try:
            amount = int(amount)
            if amount <= 0:
                return await ctx.send("No.")
        except Exception:
            amount.lower()
            if amount == "all":
                pass
            else:
                return await ctx.send(f"Usage: `{self.bot.prefix}deposit (amount)`")

        data = await self.bot.inventories.find(ctx.author.id)

        if data is None:
            return await ctx.send(
                f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")

        balance = data["balance"]
        bankbalance = data["bankbalance"]
        banklimit = data["banklimit"]
        if amount == "all":
            amount = int(balance)

        if banklimit == 0:
            return await ctx.send(f"A **:bank: Bank Slot** hasn't been bought yet. Do `{self.bot.prefix}banks`.")

        if bankbalance == banklimit:
            return await ctx.send(
                "Your bank balance is full with $`{:,}`. Purchase a larger bank slot at `{}banks`.".format(bankbalance,
                                                                                                           self.bot.prefix))

        if balance == 0:
            return await ctx.send("Your balance is empty.")

        if amount + bankbalance > banklimit:
            return await ctx.send(
                "This would put your bank balance over $`{:,}` which is your limit. Increase this limit by purchasing a larger bank slot at `{}banks`.".format(
                    banklimit, self.bot.prefix))

        if amount > balance:
            return await ctx.send("You only have $`{:,}` available to deposit.".format(balance))

        balance -= amount
        bankbalance += amount
        await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": balance})
        await self.bot.inventories.upsert({"_id": ctx.author.id, "bankbalance": bankbalance})
        embed = discord.Embed(title=":bank: Deposit Successful",
                              description="$`{:,}` has been deposited\nBank balance: $`{:,}`/`{:,}`\nBalance: $`{:,}`".format(
                                  amount, bankbalance, banklimit, balance), color=discord.Color.gold())
        await ctx.send(embed=embed)

    @deposit.error
    async def deposit_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Usage: `{self.bot.prefix}deposit (amount)`")

    @commands.command()
    async def withdraw(self, ctx, amount="null"):
        try:
            amount = int(amount)
            if amount <= 0:
                return await ctx.send("No.")
        except Exception:
            amount.lower()
            if amount == "all":
                pass
            else:
                return await ctx.send(f"Usage: `{self.bot.prefix}withdraw (amount)`")

        data = await self.bot.inventories.find(ctx.author.id)

        if data is None:
            return await ctx.send(
                f"You haven't initialized your inventory yet.  Do `{self.bot.prefix}inv` to get started!")

        balance = data["balance"]
        bankbalance = data["bankbalance"]
        banklimit = data["banklimit"]
        if amount == "all":
            amount = int(bankbalance)

        if banklimit == 0:
            return await ctx.send(f"A **:bank: Bank Slot** hasn't been bought yet. Do `{self.bot.prefix}banks`.")

        if amount > bankbalance:
            return await ctx.send("Insufficient funds. You only have $`{:,}` stored in your bank.".format(bankbalance))

        bankbalance -= amount
        balance += amount
        await self.bot.inventories.upsert({"_id": ctx.author.id, "balance": balance})
        await self.bot.inventories.upsert({"_id": ctx.author.id, "bankbalance": bankbalance})
        embed = discord.Embed(title=":bank: Withdrawal Successful",
                              description="$`{:,}` has been withdrawn\nBank balance: $`{:,}`/`{:,}`\nBalance: $`{:,}`".format(
                                  amount, bankbalance, banklimit, balance), color=discord.Color.gold())
        await ctx.send(embed=embed)

    @withdraw.error
    async def withdraw_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Usage: `{self.bot.prefix}withdraw (amount)`")


def setup(bot):
    bot.add_cog(Economy(bot))
