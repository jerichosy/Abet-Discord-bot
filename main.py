# Check: ~~dependencies~~, ~~comments~~
# Change: migrate from requests to non-blocking alternative (will not do rn)
# Additions: Categorize cmds so it shows up nicely on &help (only some, will do others next time), ~~add their respective desc~~

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
import aiohttp
import requests
import json
import random
from datetime import datetime
import time

help_command = commands.DefaultHelpCommand(
  no_category = 'List of commands'
)

bot = commands.Bot(command_prefix=commands.when_mentioned_or('&'), activity=discord.Game(name='"Technically Updated"'), help_command = help_command)  # , description=description

# PLS FIX THIS SHIT
# NOTE: There's no need to do case-insensitive checking cause bot already replies too much.
sad_words = ["sad", "depressed", "bitch", "hirap"]

genshin_words = ["mihoyo", "Mihoyo"]

yay_words = ["yay"]

#"roll" should work
primo_words = ["should i pull", "pulling", " roll", "roll ", " roll ", "constellation", "primos", "primogem", "C6", "C2", "C1"]

starter_encouragements = [
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

yay_encouragements = [
  "I’m so proud of you!",
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
  "I knew you could do it!"
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
  "Bakit ako tinatanong niyo? May Carl kayo diba?"
]

primo_response = [
  "Looks like someone's pulling today!",
  "I swear a 10 pull seems great right now",  # Unhealthy
  "What's the worse that could happen? You getting Qiqi?",
  "Maybe it's time to pull in the weapon banner",  # Unhealthy
  "Don't save your gems you'll get qiqi anyways",
  "wait don't tell me you're not going to pull?",  # Unhealthy
  "I hear that standing in the corner of mondstadt gives you a higher chance to pull a 5 star",
  "the adventurer's guild is calling. They want to watch you pull.",
  "make sure you stream if you pull.",
  "It's just a game. Pulling won't be the end of the world.",
  "New content?",
  "The Kyoya Intelligence Agency (KIA) will be monitoring your pulls."
]

genshin_response = [
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

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
characters = [
  "Fischl Xiangling",
  "Beidou Noelle",
  "Ningguang Xingqiu",
  "Razor Amber",
  "Bennett Lisa",
  "Barbara Kaeya"
]

# Do we need to catch exceptions for requests/aiohttp and send an error msg?
# Figure out aiohttp: https://discordpy.readthedocs.io/en/stable/faq.html#what-does-blocking-mean
def get_quote():
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]['q'] + " -" + json_data[0]['a']
  return(quote)

# This has issues on IPv6 networks it seems like
def get_waifu(type, category):
  url_string = "https://api.waifu.pics/"
  url_string = url_string + type + "/" + category
  response = requests.get(url_string, timeout=7)  # This can take a while. How can we make sure it doesn't block execution?
  print(response) # debug
  json_data = json.loads(response.text)
  waifu = json_data['url']
  return(waifu)

@bot.event
async def on_ready():
  print("We have logged in as {0.user}".format(bot))

@bot.command(aliases=['info', 'sourcecode', 'github', 'Github', 'GitHub'])
async def about(ctx):
  """link to documentation & source code on GitHub"""
  await ctx.send("Source code & documentation: https://github.com/jerichosy/Abet-Discord-bot")

@bot.command()
async def ping(ctx):
  """Returns ping and API/websocket latency"""
  start_time = time.time()
  to_edit = await ctx.send("Testing ping...")
  end_time = time.time()

  await to_edit.edit(content=f"Pong! {round(bot.latency * 1000)}ms | API: {round((end_time - start_time) * 1000)}ms")

@bot.command(aliases=['Carl', 'fuckcarl', 'fuckCarl'])
async def carl(ctx):
  """Dish Carl"""
  await ctx.send("https://cdn.discordapp.com/attachments/731542246951747594/905830644607758416/abet_bot.png")

@bot.command(aliases=['inspiration', 'inspo'])
async def inspire(ctx):
  """Sends a random inspirational quote"""
  async with ctx.typing():
    quote = get_quote()
    await asyncio.sleep(1)
  await ctx.send(quote)

@bot.command()
async def waifu(ctx):
  await ctx.send(get_waifu("sfw", "waifu"))

@bot.command()
async def neko(ctx):
  await ctx.send(get_waifu("sfw", "neko"))

@bot.command()
async def shinobu(ctx):
  await ctx.send(get_waifu("sfw", "shinobu"))

@bot.command()
async def megumin(ctx):
  await ctx.send(get_waifu("sfw", "megumin"))

@bot.command()
async def bully(ctx):
  await ctx.send(get_waifu("sfw", "bully"))

@bot.command()
async def cry(ctx):
  await ctx.send(get_waifu("sfw", "cry"))

@bot.command()
async def awoo(ctx):
  await ctx.send(get_waifu("sfw", "awoo"))

@bot.command()
async def smug(ctx):
  await ctx.send(get_waifu("sfw", "smug"))

@bot.command()
async def blush(ctx):
  await ctx.send(get_waifu("sfw", "blush"))

@bot.command()
async def smile(ctx):
  await ctx.send(get_waifu("sfw", "smile"))

@bot.command()
async def nom(ctx):
  await ctx.send(get_waifu("sfw", "nom"))

@bot.command()
async def happy(ctx):
  await ctx.send(get_waifu("sfw", "happy"))

@bot.command()
async def dance(ctx):
  await ctx.send(get_waifu("sfw", "dance"))

@bot.command()
async def cringe(ctx):
  await ctx.send(get_waifu("sfw", "cringe"))

# --- NSFW Start ---
@bot.command(aliases=['Hentai'])
@commands.is_nsfw()
async def hentai(ctx):
  """( ͡° ͜ʖ ͡°)"""
  #await ctx.send()
  await ctx.send(get_waifu("nsfw", "waifu"))

# Do we need to add the rest?

# --- NSFW End ---

@bot.command(aliases=['meow'])
async def cat(ctx):
  """Sends a random cat image"""
  async with aiohttp.ClientSession() as session:
    async with session.get('http://aws.random.cat/meow') as r:
        if r.status == 200:
            js = await r.json()
            await ctx.send(js['file'])

@bot.command(aliases=['Abet'])
async def abet(ctx):
  """customized Magic 8-Ball"""
  await ctx.send(random.choice(abet_response))

@bot.command()
async def choose(ctx):  # , *choices: str
  """Returns a random choice from the given words/phrases"""
  #await ctx.send(random.choice(choices))
  choose_phrases = ctx.message.content[8:].split(", ")  # Split returns a list (square brackets)
  print("\n", choose_phrases)
  await ctx.send(random.choice(choose_phrases))

@bot.command(aliases=['coin', 'flipacoin', 'heads', 'tails'])
async def coinflip(ctx):
  """Flip a coin"""
  await ctx.send(random.choice(['Heads', 'Tails']))

# Refrain from using the ff. built-in terms such as but not limited to: str, dict, list, range
# Note to self: Don't send msg in a coding block to retain markdown support
# Strictly speaking, the shop resets at 4 AM so this can mislead someone. I'll work on it when it seems needed.
@bot.command(aliases=["paimonsbargains", "paimon'sbargains", "viewshop"])
async def paimonbargains(ctx):
  """Views current Paimon's Bargains items for the month"""
  current_month = datetime.now().month

  def determine_character():
    if current_month > 6:
      return current_month - 6
    else:
      return current_month

  # Even if this function is only relevant to display_future(), do not nest functions unless there's a specific reason to do so
  def loopback(current, upper_limit):
    if current > upper_limit:
      return current - upper_limit
    else:
      return current

  def display_future():
    built = "\n\n**Future:**\n"
    for x in range(1, 7):
      built = built + months[loopback(current_month + x, 12) - 1] + " | " + characters[loopback(determine_character() + x, 6) - 1] + "\n"

    return built;

  def determine_weapon_series():
    return "\n  Blackcliff series" if current_month % 2 else "\n  Royal series"

  await ctx.send(
    "**Current:**\n"
    + months[current_month - 1] + " | " + characters[determine_character() - 1]
    + determine_weapon_series()
    + display_future()
  )

@bot.event
async def on_message(message):
  if message.author == bot.user:
    return

  msg = message.content

  # --- NEW WAIFU.PICS CMDS AFTER THIS SHOULD HAVE INTERACTION ---

  #elif message.content.startswith("&pat"):
    #waifu = get_waifu("sfw", "pat")
    #await message.channel.send(

  #elif message.content.startswith("&kiss"):
    #await message.channel.send(get_waifu("sfw", "kiss"))

  #elif message.content.startswith("&lick"):
    #await message.channel.send(get_waifu("sfw", "lick"))

  # --- END ---

  #if message.content.startswith("&say "):
  #  try:
  #    channel_id_input = int(msg[5:23])
  #  except ValueError:
  #    await message.channel.send("ERROR!")
  #  else:
  #    channel = bot.get_channel(channel_id_input)
  #    await channel.send(msg[24:])

  if any(word in msg for word in sad_words):
    await message.channel.send(random.choice(starter_encouragements))

  if any(word in msg for word in yay_words):
    await message.channel.send(random.choice(yay_encouragements))

  if any(word in msg for word in primo_words):
    await message.channel.send(random.choice(primo_response))

  if any(word in msg for word in genshin_words):
    await message.channel.send(random.choice(genshin_response))

  await bot.process_commands(message)

# Command error msg sender
@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.errors.NSFWChannelRequired):
    # Raise exception if NSFW channel setting disabled
    await ctx.send("This is an NSFW command! Please use in the appropriate channel(s).")
  elif isinstance(error, commands.errors.CommandNotFound):
    pass
  else:
    await ctx.send(error)
  # add more?

load_dotenv()
bot.run(os.getenv('BOT_TOKEN'))
