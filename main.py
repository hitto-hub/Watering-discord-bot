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

# Message
Message_val = int(json.loads(requests.get(url + "/val").text)["num_results"])

# notice id
noticeid = len(json.loads(requests.get(url + "/notice").text)["data"])

# Botの大元となるオブジェクトを生成する
bot = discord.Bot(
        intents=discord.Intents.all(),  # 全てのインテンツを利用できるようにする
        activity=discord.Game("Discord Bot入門"),  # "〇〇をプレイ中"の"〇〇"を設定,
)

# 起動時に自動的に動くメソッド
@bot.event
async def on_ready():
    # 起動すると、実行したターミナルに"Hello!"と表示される
    print("Hello!")
    for channel in bot.get_all_channels():
        if int(channel.id) == int(valchannelid):
            await channel.send(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()) + ":起動しました\n")

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
    global Message_val
    # 完全に起動するまで待つ <- 要改善
    await bot.wait_until_ready()
    # リクエストを送信
    response = requests.get(url + "/val")
    # channel指定 要改善
    for channel in bot.get_all_channels():
        if int(channel.id) == int(valchannelid):
            # メッセージ指定 要改善
            async for message in channel.history(limit=1):
                # 自分のメッセージのみを編集
                if message.author == bot.user:
                    data = json.loads(response.text)
                    for entry in data["data"]:
                        # Message[id]が存在しない場合、Message[id]に格納
                        if Message_val < int(entry['id']):
                            Message_val = int(entry['id'])
                            mes = f"{entry['timestamp']} : {entry['val']}\n"
                            await channel.send(mes)

@tasks.loop(seconds=10)
async def get_notice():
    global noticeid
    await bot.wait_until_ready()
    response = requests.get(url + "/notice")
    print("-----noticeはじめ-----")
    print(response.text)
    print(response.status_code)
    print("-----noticeおわり-----")
    data = json.loads(response.text)
    if noticeid == len(data["data"]):
        print("ifの世界線")
        return
    print("elseの世界線")
    noticeid = len(data["data"])
    # mes = f"{data['data'][-1]['timestamp']} : {data['data'][-1]['notice']}\n"
    # # noticechannelidにメッセージを送信
    # for channel in bot.get_all_channels():
    #     if int(channel.id) == int(noticechannelid):
    #         await channel.send(f"```{mes}```")
    if data["data"][-1]["notice"] == 1:
        for channel in bot.get_all_channels():
            if int(channel.id) == int(noticechannelid):
                await channel.send(f"```{data['data'][-1]['timestamp']} : 水やり開始```")
    else:
        for channel in bot.get_all_channels():
            if int(channel.id) == int(noticechannelid):
                await channel.send(f"```{data['data'][-1]['timestamp']} : 水やり停止```")

get_val.start()
get_notice.start()

# Botを起動
bot.run(token)
