import os
import random
# Pycordを読み込む
import discord
import dotenv
import requests
from discord.ext import commands,tasks
import time
import json
# from requests.packages.urllib3.exceptions import InsecureRequestWarning

# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# アクセストークンを設定
dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
# url
# httpsではpost出来ない例あり
# 関連)https://community.cloudflare.com/t/cloudflared-tunnel-receives-post-request-as-get/581874
url = str(os.getenv("API_URL"))

# channelid
# val
valchannelid = str(os.getenv("VAL_CHANNEL_ID"))
# notice
noticechannelid = str(os.getenv("NOTICE_CHANNEL_ID"))

num_val = 0
num_notice = 0
watering_time = []

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
    data = {"flag": 1}
    flag_url = url + "/flag"
    try:
        response = requests.post(flag_url, json=data)
    except:
        await ctx.respond(f"Error: 水やり指示の送信に失敗しました")
        return
    # print(response.status_code)
    # print(response.text)
    await ctx.respond(f"水やり指示を出しました")

@bot.command(name="wateringregular", description="水やりを予約関連")
async def wateringregular(ctx: discord.ApplicationContext,
                            subcommand: discord.Option(str, "subcommandを入力してください", name="subcommand", choices=["add", "delete", "list"]),
                            settime: discord.Option(str, "時間\"HH:MM\"を入力してください(省略可)", name="time", required=False, default="all"),
                            weekday: discord.Option(str, "曜日を入力してください(省略可)", name="weekday", required=False, default="all", choices=["mon", "tue", "wed", "thu", "fri", "sat", "sun", "all"]),
                            ):
    # addの場合
    if subcommand == "add":
        watering_time.append(settime + " " + weekday)
        await ctx.respond(f"水やりを予約しました\n{watering_time}")
    # deleteの場合
    elif subcommand == "delete":
        if settime == "all" and weekday == "all":
            watering_time.clear()
            await ctx.respond(f"水やり予約を全て削除しました")
        else:
            if settime + " " + weekday in watering_time:
                watering_time.remove(settime + " " + weekday)
                await ctx.respond(f"水やり予約を削除しました\n{watering_time}")
            else:
                await ctx.respond(f"水やり予約が見つかりませんでした")
    # listの場合
    elif subcommand == "list":
        await ctx.respond(f"水やり予約リスト\n{watering_time}")

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
            # print(num_val, len(data["data"]))
            if num_val > len(data["data"]):
                num_val = int(json.loads(requests.get(url + "/val").text)["num_results"])
                print("Error: get_val, valがリセットされました")
                # print(num_val, len(data["data"]))
                return

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
                try:
                    if data["data"][num_notice - 1]["notice"] == 1:
                        await channel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やり開始```")
                    elif data["data"][num_notice - 1]["notice"] == 0:
                        await channel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やり終了```")
                    else:
                        await channel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やりtimeout```")
                except:
                    print("Error: get_notice, noticeがリセットされました")
                    num_notice = len(data["data"])

@tasks.loop(seconds=55)
# 指定時間に水やり指示を送信
async def post_flag():
    # @bot.event on_readyが呼ばれるまで待つ
    await bot.wait_until_ready()
    # 時間を取得
    now = time.strftime("%H:%M", time.localtime())
    # 曜日を取得
    weekday = time.strftime("%a", time.localtime()).lower()
    print(now, weekday)
    # 水やり予約がある場合
    if len(watering_time) > 0:
        for watering_time_slot in watering_time:
            if watering_time_slot.split(" ")[0] == now and (watering_time_slot.split(" ")[1] == weekday or watering_time_slot.split(" ")[1] == "all"):
                data = {"flag": 1}
                flag_url = url + "/flag"
                try:
                    response = requests.post(flag_url, json=data)
                except:
                    for channel in bot.get_all_channels():
                        if int(channel.id) == int(valchannelid):
                            await channel.send(f"Error: 水やり指示の送信に失敗しました")
                    return
                for channel in bot.get_all_channels():
                    if int(channel.id) == int(valchannelid):
                        await channel.send(f"水やり指示を出しました")
                return

get_val.start()
get_notice.start()
post_flag.start()

# Botを起動
bot.run(token)
