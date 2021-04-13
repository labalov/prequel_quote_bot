# bot.py
import os
import re
import cv2

import discord
from dotenv import load_dotenv

from PIL import Image, ImageFont, ImageDraw


def addCaption(filename, text, percentage=0.8, outname = 'frame_out.jpg'):
    im = Image.open(filename)
    _draw = ImageDraw.Draw(im)
    _font = ImageFont.truetype("OpenSans-SemiBold.ttf", 48) # Download from https://fonts.google.com/specimen/Open+Sans
    W, H = im.size
    w, h = _draw.textsize(text, font=_font)
    _draw.text(((W-w)/2+4,(H-h)*percentage+4), text, font=_font, fill="black")
    _draw.text(((W-w)/2,(H-h)*percentage), text, font=_font, fill="white")
    im.save(outname)

def getFrame(video, sec):
    video.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
    hasFrames,image = video.read()
    print(hasFrames)
    if hasFrames:
        cv2.imwrite("frame.jpg", image)     # save 
    return hasFrames

#00:02:59,399
def timestamp_to_sec(stamp):
    print(stamp)
    print(stamp[0:2])
    hour = int(stamp[0:2])
    minute = int(stamp[3:5])
    second = int(stamp[6:8])
    millis = int(stamp[9:12])
    return 3600*hour + 60*minute + second + millis/1000


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()
enc = 'ISO-8859-1'
vidcap_array = [cv2.VideoCapture('movies/1.mp4'), cv2.VideoCapture('movies/2.mp4'), cv2.VideoCapture('movies/3.mp4')]
subtitles_array = [open('./movies/1.srt', 'r', encoding=enc).read().lower(), open('./movies/2.srt', 'r', encoding=enc).read().lower(), open('./movies/3.srt', 'r', encoding=enc).read().lower()]

@client.event
async def on_ready():
    for guild in client.guilds:
        print (guild)
#!quote 00:02:59,399
@client.event
async def on_message(message):
    print(message)
    print(message.content)
    exists = False
    if re.search("^!quote", message.content):
        for i in range(0, 3):
            subtitles = subtitles_array[i]
            quote_raw = message.content[7:]
            quote = quote_raw.lower().replace(" ", "")
            #quote_regex = "..:..:..,... \-\-> ..:..:..,...(.|\s)*"
            quote_regex = ""
            for element in quote:
                quote_regex += element
                quote_regex += "\W*"
            
            if re.search(quote_regex, subtitles) and exists == False:
                last = re.search(quote_regex, subtitles).start()
                print(last)

                if re.search("(?s:.*)-->", subtitles[0:last]):
                    indicator = re.search("(?s:.*)-->", subtitles[0:last]).end()
            
                    print (subtitles[indicator+1: indicator + 13])
                    print (subtitles[indicator - 16: indicator - 4])

                    average = (timestamp_to_sec(subtitles[indicator+1: indicator+13]) + timestamp_to_sec(subtitles[indicator-16: indicator-4]))/2
                    getFrame(vidcap_array[i], average)
                    addCaption('frame.jpg', quote_raw)
                    await message.channel.send(file=discord.File('frame_out.jpg'))
                    exists = True

        if exists == False:
            await message.channel.send("These aren't the quotes you are looking for.")

client.run(TOKEN)
#<Message id=830811270453264446 channel=<TextChannel id=188223698786975744 name='general' position=0 nsfw=False news=False category_id=None> type=<MessageType.default: 0> author=<Member id=156536977766744066 name='Gürkan' discriminator='5338' bot=False nick='Gürkan' guild=<Guild id=188223698786975744 name='labalov' shard_id=None chunked=False member_count=32>> flags=<MessageFlags value=0>>
