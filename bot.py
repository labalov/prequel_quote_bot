# bot.py
import os
import re
import cv2

import discord
from dotenv import load_dotenv

from PIL import Image, ImageFont, ImageDraw
import textwrap
import numpy as np
from fuzzysearch import find_near_matches

def get_fuzzy_search(input_text, subtitle_data, max_dist = 5):
    match_str = find_near_matches(input_text, subtitle_data, max_l_dist = max_dist)
    if len(match_str)>0:
        return match_str[0].start
    else:
        return -1

def addCaption(filename, text, percentage=0.8, outname = 'frame_out.jpg'):
    im = Image.open(filename)
    _draw = ImageDraw.Draw(im)
    _font = ImageFont.truetype("OpenSans-SemiBold.ttf", 48) # Download from https://fonts.google.com/specimen/Open+Sans
    W, H = im.size
    w, h = _draw.textsize(text, font=_font)
    avg_width = _font.getsize(text)[0] / len(text)
    textwrapper = textwrap.TextWrapper(width = int(np.round(percentage*W/avg_width)))
    out_text = textwrapper.wrap(text)
    max_len = 0
    for i in out_text:
        if len(i)>max_len:
            max_len = len(i)
            w, h = _draw.textsize(i, font=_font)
    out_text = '\n'.join(out_text)
    _draw.text(((W-w)/2+4,(H-h)*percentage+4), out_text, align='center', font=_font, fill="black")
    _draw.text(((W-w)/2,(H-h)*percentage), out_text, align='center', font=_font, fill="white")
    im.save(outname)

def getFrame(video, sec):
    video.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
    hasFrames,image = video.read()
    print(hasFrames)
    if hasFrames:
        cv2.imwrite("frame.jpg", image)     # save 
    return hasFrames

def timestamp_to_sec(stamp):
    print(stamp)
    print(stamp[0:2])
    hour = int(stamp[0:2])
    minute = int(stamp[3:5])
    second = int(stamp[6:8])
    millis = int(stamp[9:12])
    return 3600*hour + 60*minute + second + millis/1000

def find_quote_timestamp(subtitle_file, quote_raw):
    quote = quote_raw.lower().replace(" ", "")
    quote_regex = ""
    for element in quote:
        quote_regex += element
        quote_regex += "\W*"
    
    if (len(quote_raw) > 20):
        quote_index = get_fuzzy_search(quote_raw, subtitle_file)
    else:
        quote_search = re.search(quote_regex, subtitle_file)
        if quote_search:
            quote_index = quote_search.start()
        else:
            quote_index = -1

    if quote_index != -1:
        indicator_index = re.search("(?s:.*)-->", subtitle_file[0:quote_index])
        if indicator_index:
            indicator = indicator_index.end()
            return (timestamp_to_sec(subtitle_file[indicator+1: indicator+13]) + timestamp_to_sec(subtitle_file[indicator-16: indicator-4]))/2
    
    return -1

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()
enc = 'ISO-8859-1'
movie_dirs = os.listdir('movies')
videos = {}
subtitles = {}

for dir in movie_dirs:
    video_array = []
    subtitle_array = []
    for file in sorted(os.listdir('movies/' + dir)):
        if file.endswith('.srt'):
            subtitle_array.append(open('./movies/' + dir + '/' + file, 'r', encoding=enc).read().lower())
        if file.endswith('.mp4'):
            video_array.append(cv2.VideoCapture(('./movies/' + dir + '/' + file)))
    
    videos[dir] = video_array
    subtitles[dir] = subtitle_array

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
        await message.channel.send('Available commands are: !' + ', !'.join(movie_dirs))
    elif re.search("^!", message.content):
        command = message.content[1:].split(' ')[0]
        quote = ' '.join(message.content[1:].split(' ')[1:])
        if command in movie_dirs:
            for i in range(0, len(videos[command])):
                quote_timestamp = find_quote_timestamp(subtitles[command][i], quote)

                if quote_timestamp != -1 and exists == False:
                        getFrame(videos[command][i], quote_timestamp)
                        addCaption('frame.jpg', quote)
                        await message.channel.send(file=discord.File('frame_out.jpg'))
                        exists = True

            if exists == False:
                await message.channel.send("These aren't the quotes you are looking for.")
        else:
            message.channel.send("That's not a valid command")

client.run(TOKEN)