import asyncio
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from telebot.util import extract_arguments
from telebot.async_telebot import AsyncTeleBot
from telebot import telebot
from spotdl import Spotdl
from spotdl.types.song import Song
import yt_dlp
import random
from pydub import AudioSegment
import os

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

CORRECT_ANSWER = "true"

async def extract_random_segment(mp3_path, output_pat):
    audio = AudioSegment.from_file(mp3_path, format="mp3")
    duration_ms = len(audio)
    if duration_ms < 15000:
        raise ValueError("Audio file is too short!")
    start_ms = random.randint(0, duration_ms - 15000)
    end_ms = start_ms + 15000
    audio_segment = audio[start_ms:end_ms]
    output_path = os.path.join(os.path.dirname(mp3_path), output_pat)
    audio_segment.export(output_path, format="mp3")
    print(f"Extracted 15s from {start_ms / 1000:.2f}s to {end_ms / 1000:.2f}s and saved to {output_path}")
    return output_path


async def download_song(song_name, output_path="downloads/%(title)s.%(ext)s"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch:{song_name}"])


bot = AsyncTeleBot('')

# Initialization
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""
SPOTIFY_REDIRECT_URI = ""

sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI
)
# spotdl = Spotdl(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)


spotify = Spotify(auth_manager=sp_oauth)

# Handle '/start' and '/help'
@bot.message_handler(commands=['start'])
async def send_welcome(message):
    text = 'Привет! Это бот-викторина по угадыванию музыки ваших любимых исполнителей!\nНапишите /game и артиста, чтобы начать игру.'
    await bot.reply_to(message, text)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(commands=['game'])
async def mainfunc(message):
    args = extract_arguments(message.text)
    a = spotify.search(args, type="artist", offset=0)
    # print(a["artists"]["items"][0])
    artist = a["artists"]["items"][0]
    print(artist)
    artist_uri = a["artists"]["items"][0]["uri"]
    # print(artist_uri)
    b = spotify.artist_top_tracks(artist_uri, country='BY')
    random_track = random.randint(0, 8)
    # c = b["tracks"][0]["external_urls"]["spotify"]
    # print(b["tracks"][0]["external_urls"]["spotify"])
    # d = Song.from_url(c)
    # print(d)
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(spotdl.download(d))
    # spotdl.download(d)
    name_of_song = b["tracks"][random_track]["name"]
    print(b["tracks"][random_track])
    await download_song(f"{name_of_song} {args}", f"downloads/{str(message.chat.id)}")
    await extract_random_segment(f"downloads/{str(message.chat.id)}.mp3", f"{str(message.chat.id)}.mp3")

    keyboard = InlineKeyboardMarkup()
    options = []
    options1 = []
    for i in range(3):
        some = random.randint(0, 8)
        options.append(b["tracks"][some]["name"])
        options1.append("false")
    randomtrue = random.randint(0, 2)
    options.insert(randomtrue, name_of_song)
    options1.insert(randomtrue, "true")
    # options = ["Неправильный трек 1", "Куок - Далеко и надолго", "Неправильный трек 2"]
    # options1 = ["Неправильный трек 1", "true", "Неправильный трек 2"]

    for i in range(3):
        keyboard.add(InlineKeyboardButton(options[i], callback_data=options1[i]))
    with open(f"downloads/{str(message.chat.id)}.mp3", "rb") as audio:
        msg = await bot.send_audio(message.chat.id, audio, caption=f"Вы выбрали артиста {args}\nУгадайте название трека!", reply_markup=keyboard)


async def process_answer(call, buttons_msg_id):
    if call.data == CORRECT_ANSWER:
        await bot.send_message(call.message.chat.id, "Вы сделали правильный выбор!")
    await bot.delete_message(call.message.chat.id, buttons_msg_id)
    await bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: True)
async def callback_query(call):
    await process_answer(call, call.message.message_id)

if __name__ == "__main__":
    asyncio.run(bot.polling())