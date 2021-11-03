import discord
from dotenv import load_dotenv
import os
import requests
import json
import random
from datetime import datetime
import asyncio

client = discord.Client()

# NOTE: There's no need to do case-insensitive checking cause bot already replies too much.
sad_words = ["sad", "depressed", "bitch"]

genshin_words = ["mihoyo", "Mihoyo"]

yay_words = ["yay"]

primo_words = ["should i pull", "pulling", "roll", "constellation", "primos", "primogem", "C6", "C2", "C1"]

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
  "Bakit ako tinatanong niyo? May carl kayo diba?"
]

primo_response = [
  "Looks like someone's pulling today!",
  "I swear a 10 pull seems great right now",
  "What's the worse that could happen? You getting Qiqi?",
  "Maybe it's time to pull in the weapon banner",
  "Don't save your gems you'll get qiqi anyways",
  "wait don't tell me you're not going to pull?",
  "I hear that standing in the corner of mondstadt gives you a higher chance to pull a 5 star",
  "the adventurer's guild is calling. They want to watch you pull.",
  "make sure you stream if you pull.",
  "It's just a game. Pulling won't be the end of the world.",
  "New content?",
  "The Kyoya Intelligence Agency (KIA) will be monitoring your pulls.",
  "Time to get Staff of Homa!",
  "I bet you will get Staff of Homa in your next 10 pull."
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

def get_quote():
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]['q'] + " -" + json_data[0]['a']
  return(quote)

@client.event
async def on_ready():
  print("We have logged in as {0.user}".format(client))

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  msg = message.content

  if message.content.startswith("$inspire"):
    async with message.channel.typing():
      quote = get_quote()
      await asyncio.sleep(1)
    #quote = get_quote()
    await message.channel.send(quote)

  elif message.content.startswith("$Abet") or message.content.startswith("$abet"):
    await message.channel.send(random.choice(abet_response))

  elif message.content.startswith("$say "):
    try:
      channelID_Input = int(msg[5:23])
    except ValueError:
      await message.channel.send("ERROR!")
    else:
      channel = client.get_channel(channelID_Input)
      await channel.send(msg[24:])

  # Refrain from using the ff. built-in terms such as but not limited to: str, dict, list, range
  # Note to self: Don't send msg in a coding block to retain markdown support
  # Strictly speaking, the shop resets at 4 AM so this can mislead someone. I'll work on it when it seems needed.
  elif message.content.startswith("$paimonbargains") or message.content.startswith("$paimonsbargains") or message.content.startswith("$paimon'sbargains") or message.content.startswith("$viewshop"):
    currentMonth = datetime.now().month
    #currentMonth = 12

    def determine_character():
      if currentMonth > 6:
        return currentMonth - 6
      else:
        return currentMonth

    # Even if this function is only relevant to display_future(), do not nest functions unless there's a specific reason to do so
    def loopback(current, upperlimit):
      if current > upperlimit:
        return current - upperlimit
      else:
        return current

    def display_future():
      built = "\n\n**Future:**\n"
      for x in range(1, 7):
        built = built + months[loopback(currentMonth + x, 12) - 1] + " | " + characters[loopback(determine_character() + x, 6) - 1] + "\n"

      return built;

    def determine_weapon_series():
      return "\n  Blackcliff series" if currentMonth % 2 else "\n  Royal series"

    await message.channel.send(
      "**Current:**\n" +
      months[currentMonth - 1] + " | " + characters[determine_character() - 1] +
      determine_weapon_series() +
      display_future()
    )

  else:
    if any(word in msg for word in sad_words):
      await message.channel.send(random.choice(starter_encouragements))

    if any(word in msg for word in yay_words):
      await message.channel.send(random.choice(yay_encouragements))

    if any(word in msg for word in primo_words):
      await message.channel.send(random.choice(primo_response))

    if any(word in msg for word in genshin_words):
      await message.channel.send(random.choice(genshin_response))

load_dotenv('.env')
client.run(os.getenv('BOT_TOKEN'))
