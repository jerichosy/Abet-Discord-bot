# Check: ~~dependencies~~, comments
# Change: migrate from requests to non-blocking alternative (only whatanime remaining), make it not respond to bots, Fix help cmd in "No Category", Consider pulling AniList info straight from Trace.moe instead to improve response time
# Additions: Add cogs and cmd desc.
# Will not fix: Error of converting int when user accidentally types argument(s) containing characters, non-ints, etc.

# Add in commit desc/comment: 

# Notes: requests has issues on IPv6 networks

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from dotenv import load_dotenv
import os
import asyncio
import io
import aiohttp
import requests
import json
import random
from random import choices
from datetime import datetime, timedelta
import time
import re

import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()

class MyNewHelp(commands.MinimalHelpCommand):
  async def send_pages(self):
    destination = self.get_destination()
    for page in self.paginator.pages:
      emby = discord.Embed(description=page, color=0xee615b)
      await destination.send(embed=emby)

bot = commands.Bot(case_insensitive=True, command_prefix=commands.when_mentioned_or('&'), activity=discord.Game(name='&saucenao'), help_command=MyNewHelp(command_attrs = {"hidden": True}))  # , description=description

sad_words = ["sad", "depressed", "hirap"]  # Removed: "bitch"

yay_words = ["yay", "freee"]

wish_words = ["should i pull", "pulling", "p\*ll", "rolls", "constellation", "constellations", "primo", "primos", "primogem", "primogems", "c6", "c5", "c4", "c3", "c2", "c1", "c0", "character", "characters"]

mhy_words = ["mihoyo"]

sad_response = [
  "Cheer up!",
  "Hang in there!",
  "You are a great person!",
  "Stay strong.",
  "Come on! You can do it!.",
  "It's okay",
  "It's okay I believe in you",
  "Maybe we'll get them next time",
  "Keep your head high",
  "It's okay don't listen to them",
  "You are the best!",
  "We'll get you Ice cream, you like that?",
  "Is there anything I can do to make you feel better?"
]

yay_response = [
  "I'm so proud of you!",
  "Good job!",
  "Keep it up!",
  "Keep up the good work!",
  "There you go!",
  "Hell yeah!",
  "Fuck, lets gooooooooo!",
  "Omg Yay!!!!!!!",
  "Let's gooooo!",
  "I can't believe it! You are amazing!",
  "WTF? Really?",
  "What the heck? Let's goooooooooo!",
  "I knew you could do it!",
  "<:letsgo:914430483176255488>",
  "<:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488>",
  "<:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488>",
  "<:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488>",
  "<:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488><:letsgo:914430483176255488>",
  "https://cdn.discordapp.com/attachments/877238195966865498/943248232807538738/988697_558224364239923_644168573_n.png"
]

wish_response = [
  "Looks like someone's pulling today!",
  "I swear a 10 pull seems great right now",  # Unhealthy
  "What's the worse that could happen? You getting Qiqi?",
  "Don't save your gems you'll get qiqi anyways",
  "wait don't tell me you're not going to pull?",  # Unhealthy
  "I hear that standing in the corner of mondstadt gives you a higher chance to pull a 5 star",
  "the adventurer's guild is calling. They want to watch you pull.",
  "make sure you stream if you pull.",
  "It's just a game. Pulling won't be the end of the world.",
  "New content?",
  "The Kyoya Intelligence Agency (KIA) will be monitoring your pulls.",
]

mhy_response = [
  "Did I hear Mihoyo? That bitch.",
  "Mihoyo loves you",
  "Awe, we're trying our best here at Mihoyo",
  "I promise to give you more primos in future patches - Mihoyo",
  "Did you just BS Mihoyo? UID Saved, sending to Mihoyo servers...",
  "Hey people at Mihoyo are just trying to do their jobs",
  "Please rate our game with a 5 star in the Play Store!",
  "Please don't leave we need you['re money]",
  "We give all the money we make at Mihoyo to Mona",
  "All funds from Mihoyo are sent straight to Zhongli's pockets",
  "We aren't ripping you off. We're just compensating Timmie which is why we couldn't get you better rewards!"
]

abet_response = [
  "Absolutely!",
  "Without a doubt!",
  "Hell Yeah!",
  "Fuck no",
  "What the fuck are these questions? *Sighs* But yes you will get what you want for some reason",
  "Dude, that's sick. It's a no though.",
  "You're chances are as high as the amount of Qiqi constellations you have",
  "Maybe, Fine. Yes.",
  "Sinasabi ng aking mahiwagang kristal it's a paking YES putangina.",
  "I heard buying KofiTreb's Coffee increases your odds",
  "If you haven't taken a bath in the past 3 days it's a yes",
  "Bruh.",
  "Hell no.",
  "My magic balls says fuck yeah!",
  "If you believe hard enough!",
  "Do I look like I care? Just kidding it's a yes I love you bro.",
  "Dude it already happened.",
  "All you have to do is try what's stopping you?",
  "I'll bet you a hundred dollars that is not going to happen",
  "Ask Jericho",
  "Ask Carl",
  "Bakit ako tinatanong niyo? May Carl kayo diba?",
  "..."
]

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
characters = [
  "Fischl Xiangling",
  "Beidou Noelle",
  "Ningguang Xingqiu",
  "Razor Amber",
  "Bennett Lisa",
  "Barbara Kaeya"
]

def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

# Do we need to catch exceptions for requests/aiohttp and send an error msg?
async def get_json_quote(url):
  #response = requests.get("https://zenquotes.io/api/random", timeout=7)
  #json_data = json.loads(response.text)
  async with aiohttp.ClientSession() as session:
    async with session.get(url) as resp:
      json_data = await resp.json()
  return json_data

async def get_waifu(type, category):
  url_string = f"https://api.waifu.pics/{type}/{category}"
  async with aiohttp.ClientSession() as session:
    async with session.get(url_string) as r:
      print(f"Waifu.pics: {r.status}") # debug
      if r.status == 200:
        json_data = await r.json()
        waifu = json_data['url']
  
  return waifu

async def get_waifu_im_embed(type, category):
  type = "False" if type=="sfw" else "True"
  url_string = f"https://api.waifu.im/random/?selected_tags={category}&is_nsfw={type}"

  async with aiohttp.ClientSession() as session:
    #start_time = time.time()
    async with session.get(url_string) as resp:
      print(f"Waifu.im: {resp.status}")
      json_data = await resp.json()
      if resp.status in {200, 201}:
        #embed = discord.Embed(color=0xffc0cb)
        embed = discord.Embed(color=int(f"0x{json_data['images'][0]['dominant_color'].lstrip('#')}", 0))
        embed.set_image(url=json_data['images'][0]['url'])

        source = json_data['images'][0]['source']

        #end_time = time.time()
        #{round((end_time - start_time) * 1000)}ms
        #embed.set_footer(text=f"Retrieved in {end_time - start_time} seconds", icon_url="https://waifu.im/favicon.ico")

        print(json_data)

      else:
        error = json_data['message']
        print(error)
  
  return source, embed

# Note: discord.Member implements a lot of func of discord.User, but we don't need any of the extras atm
async def get_roleplay_embed(ctx, user_mentioned, type, category, action):
  title = f"{ctx.author.name} {action} "
  if user_mentioned is not None:  # PEP 8
    name = str(user_mentioned)
    size = len(name)
    title += name[:size-5]
  embed = discord.Embed(title=title, color=0xee615b)
  embed.set_image(url=await get_waifu(type, category))
  return embed

def coin_flip():
  population = ['Heads', 'Tails']
  weight = [0.1, 0.9]
  return str(choices(population, weight)).strip('[\']')

@bot.event
async def on_ready():
  print("We have logged in as {0.user}".format(bot))

class Info(commands.Cog):
  
  def __init__(self, bot):
    self.bot = bot

  @commands.command(aliases=['info', 'sourcecode', 'github'])
  async def about(self, ctx):
    """link to documentation & source code on GitHub"""
    await ctx.send("Source code & documentation: https://github.com/jerichosy/Abet-Discord-bot")

  @commands.command(aliases=['code'])
  async def showcode(self, ctx):
    """Have the bot upload it's own sourcecode here in Discord"""
    await ctx.send(file=discord.File('main.py'))

  @commands.command()
  async def ping(self, ctx):
    """Get the bot's current websocket and API latency"""
    start_time = time.time()
    to_edit = await ctx.send("Testing ping...")
    end_time = time.time()
    await to_edit.edit(content=f"Pong! {round(bot.latency * 1000)}ms | API: {round((end_time - start_time) * 1000)}ms")

class Fun(commands.Cog):
  
  def __init__(self, bot):
    self.bot = bot

  # Don't make this into an embed
  @commands.command(aliases=['fuckcarl'])
  async def carl(self, ctx):
    """Dish Carl"""
    await ctx.send("https://cdn.discordapp.com/attachments/731542246951747594/905830644607758416/abet_bot.png")

  @commands.command(aliases=['inspiration', 'inspo', 'quote'])
  async def inspire(self, ctx):
    """Sends a random inspirational quote"""
    async with ctx.typing():
      json_data = await get_json_quote("https://zenquotes.io/api/random")
      quote = json_data[0]['q'] + " -" + json_data[0]['a']
      await asyncio.sleep(1)
    await ctx.send(quote)

  @commands.command(aliases=['west', 'kanyewest', 'ye'])
  async def kanye(self, ctx):
    """random Kanye West quotes (Kanye as a Service)"""
    async with ctx.typing():
      json_data = await get_json_quote("https://api.kanye.rest/")
      quote = json_data['quote'] + " - Kanye West"
    await ctx.send(quote)

  @commands.command(aliases=['tronald', 'dump', 'donaldtrump', 'tronalddump'])
  async def trump(self, ctx):
    """random dumbest things Donald Trump has ever said"""
    async with ctx.typing():
      json_data = await get_json_quote("https://api.tronalddump.io/random/quote")
      quote = json_data['value'] + " - Donald Trump"

      # If there's a link in the msg, make it not embed
      #def Find(string):
      #  regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
      #  url = re.findall(regex, string)
      #  return [x[0] for x in url]

      # Test the above function
      #quote = 'Huma calls it a "MESS," the rest of us call it CORRUPT! WikiLeaks catches Crooked in the act - again. #DrainTheSwamp https://t.co/juvdLIJPWu - Donald Trump'

      #extracted_url = str(Find(quote)).strip('[\']')
      #quote = quote.replace(extracted_url, f"<{extracted_url}>")
      #print(quote)

    await ctx.send(quote)

  @commands.command(aliases=['tronaldmeme', 'dumpmeme', 'donaldtrumpmeme', 'tronalddumpmeme'])
  async def trumpmeme(self, ctx):
    """random dumbest things Donald Trump has ever said"""
    async with ctx.typing():
      async with aiohttp.ClientSession() as session:
        async with session.get('https://api.tronalddump.io/random/meme') as r:
          data = io.BytesIO(await r.read())
          await ctx.send(file=discord.File(data, "tronalddump.jpg"))

  @commands.command(aliases=['meow'])
  async def cat(self, ctx):
    """Sends a random cat image"""
    async with aiohttp.ClientSession() as session:
      async with session.get('http://aws.random.cat/meow') as r:
        if r.status == 200:
          js = await r.json()
          await ctx.send(js['file'])

  # Lifted from https://github.com/Rapptz/discord.py/blob/master/examples/guessing_game.py
  @commands.command(aliases=['game'])
  async def guess(self, ctx):
    await ctx.send('Guess a number between 1 and 10.')

    def is_correct(m):
      return m.author == ctx.author and m.content.isdigit()

    answer = random.randint(1, 10)

    try:
      guess = await bot.wait_for('message', check=is_correct, timeout=5.0)
    except asyncio.TimeoutError:
      return await ctx.send(f'Sorry, you took too long it was {answer}.')

    if int(guess.content) == answer:
      await ctx.send('You are right!')
    else:
      await ctx.send(f'Oops. It is actually {answer}.')

class Waifu(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def waifu(self, ctx):
    await ctx.send(await get_waifu("sfw", "waifu"))

  @commands.command()
  async def neko(self, ctx):
    await ctx.send(await get_waifu("sfw", "neko"))

  @commands.command()
  async def shinobu(self, ctx):
    await ctx.send(await get_waifu("sfw", "shinobu"))

  @commands.command()
  async def megumin(self, ctx):
    await ctx.send(await get_waifu("sfw", "megumin"))

  @commands.command()
  async def bully(self, ctx):
    await ctx.send(await get_waifu("sfw", "bully"))

  @commands.command()
  async def cry(self, ctx):
    await ctx.send(await get_waifu("sfw", "cry"))

  @commands.command()
  async def awoo(self, ctx):
    await ctx.send(await get_waifu("sfw", "awoo"))

  @commands.command()
  async def smug(self, ctx):
    await ctx.send(await get_waifu("sfw", "smug"))

  @commands.command()
  async def blush(self, ctx):
    await ctx.send(await get_waifu("sfw", "blush"))

  @commands.command()
  async def smile(self, ctx):
    await ctx.send(await get_waifu("sfw", "smile"))

  @commands.command()
  async def nom(self, ctx):
    await ctx.send(await get_waifu("sfw", "nom"))

  @commands.command()
  async def happy(self, ctx):
    await ctx.send(await get_waifu("sfw", "happy"))

  @commands.command()
  async def dance(self, ctx):
    await ctx.send(await get_waifu("sfw", "dance"))

  @commands.command()
  async def cringe(self, ctx):
    await ctx.send(await get_waifu("sfw", "cringe"))

  @commands.command()
  async def maid(self, ctx):
    #text1, text2 = await get_waifu_im_embed("sfw", "maid")
    #await ctx.send(text1 + "\n" + text2)
    text, embed = await get_waifu_im_embed("sfw", "maid")
    await ctx.send(text, embed=embed)

  @commands.command()
  async def waifu2(self, ctx):
    text, embed = await get_waifu_im_embed("sfw", "waifu")
    await ctx.send(text, embed=embed)

class Roleplay(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  # Note: discord.Member implements a lot of func of discord.User, but we don't need any of the extras atm
  @commands.command()
  async def cuddle(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "cuddle", "cuddles"))

  @commands.command()
  async def hug(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "hug", "hugs"))

  @commands.command()
  async def kiss(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "kiss", "kisses"))

  @commands.command()
  async def lick(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "lick", "licks"))

  @commands.command()
  async def pat(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "pat", "pats"))

  @commands.command()
  async def bonk(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "bonk", "bonks"))

  @commands.command()
  async def yeet(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "yeet", "yeets"))

  @commands.command()
  async def wave(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "wave", "waves"))

  @commands.command()
  async def highfive(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "highfive", "highfives"))

  @commands.command()
  async def handhold(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "handhold", "handholds"))

  @commands.command()
  async def bite(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "bite", "bites"))

  @commands.command()
  async def glomp(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "glomp", "glomps"))

  @commands.command()
  async def slap(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "slap", "slaps"))

  # Add kill Abet bot easter egg (go offline then back on and send some scary/taunting shit)
  @commands.command()
  async def kill(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "kill", "kills"))

  @commands.command()
  async def kick(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "kick", "kicks"))

  @commands.command()
  async def wink(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "wink", "winks at"))

  @commands.command()
  async def poke(self, ctx, user_mentioned: discord.User=None):
    await ctx.send(embed=await get_roleplay_embed(ctx, user_mentioned, "sfw", "poke", "pokes"))

# --- NSFW Start ---
class NSFW(commands.Cog):
  
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  @commands.is_nsfw()
  async def hentai(self, ctx):
    """( ͡° ͜ʖ ͡°)"""
    await ctx.send(await get_waifu("nsfw", "waifu"))

  @commands.command()
  @commands.is_nsfw()
  async def nekonsfw(self, ctx):
    await ctx.send(await get_waifu("nsfw", "neko"))

  @commands.command()
  @commands.is_nsfw()
  async def trap(self, ctx):
    await ctx.send(await get_waifu("nsfw", "trap"))

  @commands.command()
  @commands.is_nsfw()
  async def blowjob(self, ctx):
    await ctx.send(await get_waifu("nsfw", "blowjob"))

  @commands.command()
  @commands.is_nsfw()
  async def ass(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "ass")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def ero(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "ero")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def hentai2(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "hentai")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def maidnsfw(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "maid")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def milf(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "milf")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def oppai(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "oppai")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def oral(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "oral")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def paizuri(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "paizuri")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def selfies(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "selfies")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def uniform(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "uniform")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def ecchi(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "ecchi")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def waifunsfw(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "waifu")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def selfies(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "selfies")
    await ctx.send(text, embed=embed)

  @commands.command()
  @commands.is_nsfw()
  async def breast(self, ctx):
    text, embed = await get_waifu_im_embed("nsfw", "breast")
    await ctx.send(text, embed=embed)

# --- NSFW End ---

class Tools(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def abet(self, ctx, has_question=None):
    """customized Magic 8-Ball"""
    if has_question is None:  # PEP 8
      await ctx.send("What?")
    else:
      await ctx.send(random.choice(abet_response))

  @commands.command()
  async def choose(self, ctx):
    """Returns a random choice from the given words/phrases"""
    choose_phrases = ctx.message.content[8:].split(", ")  # Split returns a list (square brackets)
    print("\n", choose_phrases)
    #print(len(choose_phrases))
    if len(choose_phrases) > 1:
      await ctx.send(random.choice(choose_phrases))
    else:
      pass

  @commands.command(aliases=['coin', 'flipacoin', 'heads', 'tails'])
  async def coinflip(self, ctx):
    """Flip a coin"""
    await ctx.send(coin_flip())

  @commands.command(aliases=['cointally', 'flipacointally', 'headstally', 'tailstally', 'countcoins', 'coincount', 'coinscount'])
  async def coinfliptally(self, ctx, amount: int):
    heads_count = 0
    tails_count = 0
    #count = []
    response = ""

    if amount > 10000:
      amount = 10000
      response += "Max of 10k only allowed!\n"

    for x in range(amount):
      #count.append(coin_flip())
      if coin_flip() == 'Heads':
        heads_count += 1
      else:
        tails_count += 1

    response += f"Heads: {heads_count}\nTails: {tails_count}"
    #await ctx.send(print(count))
    await ctx.send(response)

  # Refrain from using the ff. built-in terms such as but not limited to: str, dict, list, range
  # Note to self: Don't send msg in a coding block to retain markdown support
  # TODO: Strictly speaking, the shop resets at 4 AM so this can mislead someone. I'll work on it when it seems needed.
  @commands.command(aliases=["paimonsbargains", "paimon'sbargains", "viewshop"])
  async def paimonbargains(self, ctx):
    """Views current Paimon's Bargains items for the month"""
    current_month = datetime.now().month

    def determine_character():
      if current_month > 6:
        return current_month - 6
      else:
        return current_month

    # Even if this function is only relevant to display_future(), do not nest functions unless there's a specific reason to do so
    def wraparound(current, upper_limit):
      if current > upper_limit:
        return current - upper_limit
      else:
        return current

    def display_future():
      built = "\n\n**Future:**\n"
      for x in range(1, 7):
        built += months[wraparound(current_month + x, 12) - 1] + " | " + characters[wraparound(determine_character() + x, 6) - 1] + "\n"

      return built;

    def determine_weapon_series():
      return "\n  Blackcliff series" if current_month % 2 else "\n  Royal series"

    await ctx.send(
      "**Current:**\n"
      + months[current_month - 1] + " | " + characters[determine_character() - 1]
      + determine_weapon_series()
      + display_future()
    )

  @commands.command(aliases=['wait', 'anime'])
  async def whatanime(self, ctx, url=None):
    """What Anime Is This"""

    if url is None and len(ctx.message.attachments) == 0:
      await ctx.send("Please attach an image / provide a link or URL")
      return

    if url is None:
      url = ctx.message.attachments[0].url
    
    async with ctx.typing():
      # consider adding search?cutBorders&url={} to https://soruly.github.io/trace.moe-api/#/docs?id=cut-black-borders
      start_time = time.time()
      response = requests.get(f"https://api.trace.moe/search?url={url}", timeout=7)
      #response = requests.get(f"https://api.trace.moe/search?anilistInfo&url={url}", timeout=7)
      #end_time = time.time()
      print(f"Trace.moe: {response}") # debug
      json_data = json.loads(response.text)

      reason = ""
      if json_data['error']:
        reason = json_data['error']
      else:  
        file_name = json_data['result'][0]['filename']
        timestamp = ""
        if json_data['result'][0]['episode'] is not None:
          timestamp = f"Episode {json_data['result'][0]['episode']} | "
        timestamp += str(timedelta(seconds=int(json_data['result'][0]['from'])))
        similarity = json_data['result'][0]['similarity']
        video_url = json_data['result'][0]['video']

        anilist_id = json_data['result'][0]['anilist']

        query = '''
        query ($id: Int) { # Define which variables will be used in the query (id)
          Media (id: $id, type: ANIME) { # Insert our variables into the query arguments (id) (type: ANIME is hard-coded in the query)
            id
            title {
              romaji
              english
              native
            }
            isAdult
          }
        }
        '''

        variables = {
            'id': anilist_id
        }

        response = requests.post("https://graphql.anilist.co/", json={'query': query, 'variables': variables})
        end_time = time.time()
        print(f"{round((end_time - start_time) * 1000)}ms")
        print(f"  AniList GraphQL API: {response}") # debug
        json_data = json.loads(response.text)

        native = "" if json_data['data']['Media']['title']['native'] is None else f"**{json_data['data']['Media']['title']['native']}**\n"
        romaji = "" if json_data['data']['Media']['title']['romaji'] is None else f"**{json_data['data']['Media']['title']['romaji']}**\n"
        english = "" if json_data['data']['Media']['title']['english'] is None else f"**{json_data['data']['Media']['title']['english']}**\n"
        #native = ""
        #romaji = ""
        #english = ""
        #title = json_data['data']['Media']['title']['native']
        #title += 

    if reason:
      # So that if the user accidentally sends a link that embeds, even if the error code were to refer (send) back the URL, it will not embed.
      # Conflicts with other error types tho
      #def Find(string):
      #  regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
      #  url = re.findall(regex, string)
      #  return [x[0] for x in url]

      #extracted_url = str(Find(reason)).strip('[\']')
      #reason = reason.replace(extracted_url, f"<{extracted_url}>")

      await ctx.send(reason)
    else:
      await ctx.send(f"<@{ctx.author.id}>\n\n{native}{romaji}{english}``{file_name}``\n{timestamp}\n{'{:.1f}'.format(similarity * 100)}% similarity")
      #await ctx.send(video_url)

      if json_data['data']['Media']['isAdult']:
        preview_file_name = "SPOILER_preview.mp4"
        warning = "[NSFW]"
      else:
        preview_file_name = "preview.mp4"
        warning = ""

      async with aiohttp.ClientSession() as session:
        async with session.get(video_url) as resp:
          if resp.status != 200:
            return await ctx.send('Could not download preview...')
          data = io.BytesIO(await resp.read())
          await ctx.send(warning, file=discord.File(data, preview_file_name))

  @commands.command(aliases=['sauce', 'source', 'getsource', 'artsource', 'getartsource'])
  async def saucenao(self, ctx, url=None):
    """SauceNao"""

    if url is None and len(ctx.message.attachments) == 0:
      await ctx.send("Please attach an image / provide a link or URL")
      return

    if url is None:
      url = ctx.message.attachments[0].url
    
    async with ctx.typing():
      token = os.getenv("SAUCENAO_TOKEN")
      #response = requests.get(f"https://saucenao.com/search.php?db=999&output_type=2&numres=1&url={url}&api_key={token}", timeout=7)
      async with aiohttp.ClientSession() as session:
        async with session.get(f"https://saucenao.com/search.php?db=999&output_type=2&numres=1&url={url}&api_key={token}") as r:
          print(f"SauceNao: {r.status}")
          json_data = await r.json()
          #print(json_data)

          # error checking
          if r.status != 200 or json_data['header']['status'] != 0:
            if json_data['header']['status'] < 0:
              if json_data['header']['status'] == -2:
                return await ctx.send("Search Rate Too High. Your IP has exceeded the basic account type's rate limit of 6 searches every 30 seconds.")
              else:
                return await ctx.send("Client side error (bad image, out of searches, etc)")
            else:
              return await ctx.send("Server side error (failed descriptor gen, failed query, etc). Please try again!")
          
          # if successful
          def get_json_field(prefix, parameter):
            try:
              field = "" if not json_data['results'][0]['data'][parameter] else f"{prefix}{json_data['results'][0]['data'][parameter]}\n"
              #print(json_data['results'][0]['data'][parameter])
            except KeyError:
              field = ""

            return field

          #source = f"**Sauce:** {json_data['results'][0]['data']['source']}\n"
          source = get_json_field("**Sauce:** ", 'source')
          if source == "":
            source = f"**Sauce:** {json_data['results'][0]['data']['ext_urls'][0]}\n"
          # to handle stuff like 
          # https://i.pximg.net/img-original/img/2021/07/28/07/50/29/91550773 with https://cdn.discordapp.com/attachments/870095545992101958/947297823945293834/lASQNdS.jpg or
          # http://i2.pixiv.net/img-original/img/2016/01/16/01/19/56/54734137 with https://cdn.discordapp.com/attachments/870095545992101958/947296081354588211/54734137_p0_master1200.png
          elif "/img-original/img/" in source:
            source = f"**Sauce:** https://pixiv.net/en/artworks/{source[len(source) - 9 : len(source)]}"
          part = get_json_field("**Part:** ", 'part')
          characters = get_json_field("**Character(s):** ", 'characters')
          #characters = "" if json_data['results'][0]['data']['characters'] is None else f"**Character(s):** {json_data['results'][0]['data']['characters']}\n"
          similarity = f"**Similarity:** {float(json_data['results'][0]['header']['similarity'])}%"

          #danbooru = "" if json_data['results'][0]['data']['danbooru_id'] is None else f"Danbooru ID: {json_data['results'][0]['data']['danbooru_id']}\n"
          danbooru = get_json_field("Danbooru ID: ", 'danbooru_id')
          #yandere = "" if json_data['results'][0]['data']['yandere_id'] is None else f"Yandere ID: {json_data['results'][0]['data']['yandere_id']}\n"
          yandere = get_json_field("Yandere ID: ", 'yandere_id')
          #gelbooru = "" if json_data['results'][0]['data']['gelbooru_id'] is None else f"Gelbooru ID: {json_data['results'][0]['data']['gelbooru_id']}\n"
          gelbooru = get_json_field("Gelbooru ID: ", 'gelbooru_id')

          separator = "" if danbooru == "" and yandere == "" and gelbooru == "" else "\n--------------------------\n"

          await ctx.send(f"<@{ctx.author.id}> Note: For anime, use &whatanime\n\n{source}{part}{characters}{similarity}{separator}{danbooru}{yandere}{gelbooru}")

  @commands.command()
  async def weather(self, ctx, location=None):
    if location is None:
      location = ""
    async with ctx.typing():
      async with aiohttp.ClientSession() as session:
        async with session.get(f"https://wttr.in/{location}?0T") as resp:
          print(f"wttr.in response: {resp.status}")
          if await resp.text() == "" or await resp.text() == "Follow @igor_chubin for wttr.in updates":
            return await ctx.send("The weather service is having problems. Please try again later.")
          await ctx.send(f"```{await resp.text()}```")
          #print (await resp.text())
      #response = requests.get(f"https://wttr.in/{location}?0")
    #print(response.text)
    #await ctx.send(f"```ansi\n{response.text}```")

  @commands.command()
  async def metar(self, ctx, airport_code):
    token = os.getenv("METAR_TOKEN")
    async with ctx.typing():
      async with aiohttp.ClientSession(headers={"Authorization": "BEARER " + token}) as session:
        async with session.get(f"https://avwx.rest/api/metar/{airport_code}") as response:
          print(f"AVWX response: {response.status}")
          json_data = await response.json()
          if response.status != 200:
            return await ctx.send(json_data['error'])
          await ctx.send(json_data['raw'])
        
  # Create command

class Admin(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command(aliases=['delete'])
  #@commands.is_owner()
  @has_permissions(manage_messages=True)
  async def purge(self, ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)

  @commands.command(aliases=['close', 'shutup', 'logoff', 'stop'])
  @has_permissions(administrator=True)
  async def shutdown(self, ctx):
    await ctx.send("🛑 Shutting down!")
    await bot.close()

  @commands.command(aliases=['setstatus'])
  @has_permissions(manage_guild=True)
  async def changestatus(self, ctx):
    status_msg = ctx.message.content[14:]
    if status_msg:
      await ctx.message.add_reaction('✅')
      await bot.change_presence(activity=discord.Game(name=status_msg))
    else:
      await ctx.send("What status would you like me to play?")

  @commands.command()
  async def sendmsg(self, ctx, channel_id: int, content):
    channel = bot.get_channel(channel_id)
    await channel.send(ctx.message.content[28:])

  @commands.command()
  async def sendreply(self, ctx, channel_id: int, message_id: int, content):
    channel = bot.get_channel(channel_id)
    message = await channel.fetch_message(message_id)
    await message.reply(ctx.message.content[50:])

@bot.event
async def on_message(message):
  if message.author == bot.user:
    return

  msg = message.content.lower()

  for x in sad_words:
    if findWholeWord(x)(msg):
        await message.channel.send(random.choice(sad_response))
        break
  
  if any(word in msg for word in yay_words):
    await message.channel.send(random.choice(yay_response))
  
  #for x in wish_words:
    #if findWholeWord(x)(msg):
        #await message.channel.send(random.choice(wish_response))
        #break
  
  #for x in mhy_words:
    #if findWholeWord(x)(msg):
        #await message.channel.send(random.choice(mhy_response))
        #break

  await bot.process_commands(message)

# Command error msg sender
@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.errors.NSFWChannelRequired):
    # Raise exception if NSFW channel setting disabled
    await ctx.send("This is an NSFW command! Please use in the appropriate channel(s).")
  #elif isinstance(error, commands.errors.MissingRequiredArgument) and (ctx.message.content.startswith("&abet") or ctx.message.content.startswith("&Abet")):
  #  await ctx.send("What?")
  #elif isinstance(error, commands.errors.CommandNotFound):
  #  pass
  elif isinstance(error, discord.HTTPException):
    await ctx.send("You are ratelimited")
  else:
    await ctx.send(error)
  # add more?

bot.add_cog(Info(bot))
bot.add_cog(Fun(bot))
bot.add_cog(Waifu(bot))
bot.add_cog(Roleplay(bot))
bot.add_cog(NSFW(bot))
bot.add_cog(Tools(bot))
bot.add_cog(Admin(bot))

bot.run(os.getenv('BOT_TOKEN'))
