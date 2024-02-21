import os
import random
# Pycordを読み込む
import discord
import dotenv
import requests
from discord.ext import commands,tasks
import time
import json

# アクセストークンを設定
dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
# gasurl
url = str(os.getenv("API_URL"))

# channelid
# val
valchannelid = str(os.getenv("VAL_CHANNEL_ID"))
# notice
noticechannelid = str(os.getenv("NOTICE_CHANNEL_ID"))

num_val = 0
num_notice = 0

# Botの大元となるオブジェクトを生成する
bot = discord.Bot(
        intents=discord.Intents.all(),  # 全てのインテンツを利用できるようにする
        activity=discord.Game("💧"),  # "〇〇をプレイ中"の"〇〇"を設定,
)

# 起動時に自動的に動くメソッド
@bot.event
async def on_ready():
    global num_val
    global num_notice
    # 起動すると、実行したターミナルに"Hello!"と表示される
    print("Hello!")
    for channel in bot.get_all_channels():
        if int(channel.id) == int(valchannelid):
            await channel.send(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()) + ":起動しました\n")
    # Message
    # notice id
    try:
        num_val = int(json.loads(requests.get(url + "/val").text)["num_results"])
        num_notice = int(json.loads(requests.get(url + "/notice").text)["num_results"])
    except:
        errmes = "Error: メッセージの取得に失敗しました"
        # メッセージの取得に失敗した場合、エラーメッセージを送信
        for channel in bot.get_all_channels():
            if int(channel.id) == int(valchannelid):
                await channel.send(errmes)


# pingコマンドを実装
@bot.command(name="ping", description="pingを返します")
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond(f"pong to {ctx.author.mention}")

# /wateringコマンドを実装
@bot.command(name="watering", description="水やりを開始します")
async def watering(ctx: discord.ApplicationContext):
    response = requests.post(url + "/flag", data={"flag": 1})
    await ctx.respond(f"水やりを開始しました")

# 10秒ごとにchannelidにメッセージを送信
# ToDo: 値の取得、表示方法を改善
@tasks.loop(seconds=10)
async def get_val():
    global num_val
    # 完全に起動するまで待つ <- 要改善
    await bot.wait_until_ready()
    # リクエストを送信
    try:
        response = requests.get(url + "/val")
        data = json.loads(response.text)
    except:
        errmes = "Error: メッセージの取得に失敗しました"
        # メッセージの取得に失敗した場合、エラーメッセージを送信
        for channel in bot.get_all_channels():
            if int(channel.id) == int(valchannelid):
                await channel.send(errmes)
        return
    # channel指定 要改善
    for channel in bot.get_all_channels():
        if int(channel.id) == int(valchannelid):
            for entry in data["data"]:
                # Message[id]が存在しない場合、Message[id]に格納
                if num_val < int(entry['id']):
                    num_val = int(entry['id'])
                    mes = f"{entry['timestamp']} : {entry['val']}\n"
                    await channel.send(mes)

@tasks.loop(seconds=10)
async def get_notice():
    global num_notice
    await bot.wait_until_ready()
    try:
        response = requests.get(url + "/notice")
        data = json.loads(response.text)
    except:
        errmes = "Error: メッセージの取得に失敗しました"
        for channel in bot.get_all_channels():
            if int(channel.id) == int(noticechannelid):
                await channel.send(errmes)
        return
    for channel in bot.get_all_channels():
        if int(channel.id) == int(noticechannelid):
            if num_notice == len(data["data"]):
                return
            else:
                num_notice += 1
                if data["data"][num_notice - 1]["notice"] == 1:
                    await channel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やり開始```")
                elif data["data"][num_notice - 1]["notice"] == 2:
                    await channel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やり中断```")
                elif data["data"][num_notice - 1]["notice"] == 0:
                    await channel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やり停止```")
                else:
                    await channel.send(f"```{data['data'][num_notice - 1]['timestamp']} : エラーが発生しました。```")

get_val.start()
get_notice.start()

# Botを起動
bot.run(token)
