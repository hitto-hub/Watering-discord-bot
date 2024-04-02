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
Valchannelid = str(os.getenv("VAL_CHANNEL_ID"))
Noticechannelid = str(os.getenv("NOTICE_CHANNEL_ID"))
Logchannelid = str(os.getenv("LOG_CHANNEL_ID"))

Valchannel = None
Noticechannel = None
Logchannel = None

num_val = 0
num_notice = 0
watering_time = set()

# Botの大元となるオブジェクトを生成する
bot = discord.Bot(
        intents=discord.Intents.all(),  # 全てのインテンツを利用できるようにする
        activity=discord.Game("💧"),  # "〇〇をプレイ中"の"〇〇"を設定,
)

wateringregular = bot.create_group(name="wateringregular", description="水やり予約関連")

def makelog(header, message):
    return f'[{time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())} : {header}] {message}'

# 起動時に自動的に動くメソッド
@bot.event
async def on_ready():
    global num_val
    global num_notice
    global Valchannel
    global Noticechannel
    global Logchannel
    # channelの取得
    for channel in bot.get_all_channels():
        if int(channel.id) == int(Valchannelid):
            Valchannel = channel
            print("Valchannelを取得しました")
        if int(channel.id) == int(Noticechannelid):
            Noticechannel = channel
            print("Noticechannelを取得しました")
        if int(channel.id) == int(Logchannelid):
            Logchannel = channel
            print("Logchannelを取得しました")
    if Valchannel is None or Noticechannel is None or Logchannel is None:
        print("Error: channelの取得に失敗しました。チャンネルIDを確認してください。")
        exit()
    try:
        num_val = int(json.loads(requests.get(url + "/val").text)["num_results"])
        num_notice = int(json.loads(requests.get(url + "/notice").text)["num_results"])
    except:
        mes = "メッセージの取得に失敗しました。apiサーバーが起動しているか確認してください。"
        await Logchannel.send(makelog("Error", mes))
        exit()
    get_val.start()
    get_notice.start()
    post_flag.start()
    # Logchannelにメッセージを送信
    mes = "正常に起動しました"
    await Logchannel.send(makelog("Info", mes))

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
        mes = "水やり指示の送信に失敗しました, apiサーバーが起動しているか確認してください"
        await ctx.respond(f"Error: {mes}")
        await Logchannel.send(makelog("Error", mes))
        return
    # print(response.status_code)
    # print(response.text)
    mes = "水やり指示を出しました"
    await ctx.respond(f"{mes}")
    await Logchannel.send(makelog("Info", mes))

@wateringregular.command(
    name="add",
    description="水やり予約を追加します"
)
async def add(ctx: discord.ApplicationContext,
                settime: discord.Option(str, "時間\"HH:MM\"を入力してください", name="time"),
                weekday: discord.Option(str, "曜日を入力してください", name="weekday", choices=["mon", "tue", "wed", "thu", "fri", "sat", "sun", "all"])):
    if settime + " " + weekday in watering_time:
        mes = "水やり予約が重複しています"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))
    else:
        watering_time.add(settime + " " + weekday)
        mes = f"水やり予約を追加しました。{watering_time}"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Info", mes))

@wateringregular.command(
    name="remove",
    description="水やり予約を削除します"
)
async def remove(ctx: discord.ApplicationContext,
                settime: discord.Option(str, "時間\"HH:MM\"を入力してください", name="time"),
                weekday: discord.Option(str, "曜日を入力してください", name="weekday", choices=["mon", "tue", "wed", "thu", "fri", "sat", "sun", "all"])):
    if settime + " " + weekday in watering_time:
        watering_time.discard(settime + " " + weekday)
        if watering_time == set():
            mes = f"水やり予約を全て削除しました。{watering_time}"
            await ctx.respond(mes)
            await Logchannel.send(makelog("Info", mes))
        else:
            mes = f"水やり予約を削除しました。{watering_time}"
            await ctx.respond(mes)
            await Logchannel.send(makelog("Info", mes))
    else:
        mes = f"指定した水やり予約({settime} {weekday})が見つかりませんでした。"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))

@wateringregular.command(
    name="list",
    description="水やり予約一覧を表示します"
)
async def list(ctx: discord.ApplicationContext):
    if len(watering_time) == 0:
        mes = "水やり予約はありません"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Info", mes))
    else:
        mes = f"水やり予約一覧{watering_time}"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Info", mes))

# 10秒ごとにchannelidにメッセージを送信
# ToDo: 値の取得、表示方法を改善
@tasks.loop(seconds=10)
async def get_val():
    global num_val
    global Valchannel
    global Logchannel
    # 起動するまで待つ
    await bot.wait_until_ready()
    # リクエストを送信
    try:
        response = requests.get(url + "/val")
        data = json.loads(response.text)
    except:
        mes = "水分量のメッセージの取得に失敗しました. apiサーバーが起動しているか確認してください."
        await Logchannel.send(makelog("Error", mes))
        return
    for entry in data["data"]:
        # Message[id]が存在しない場合、Message[id]に格納
        if num_val < int(entry['id']):
            num_val = int(entry['id'])
            mes = f"{entry['timestamp']} : {entry['val']}"
            await Valchannel.send(mes)
    # print(num_val, len(data["data"]))
    if num_val > len(data["data"]):
        num_val = int(json.loads(requests.get(url + "/val").text)["num_results"])
        mes = "get_val, valがリセットされました.データベースがリセットされました."
        print(f"Error: {mes}")
        await Logchannel.send(makelog("Error", mes))
        # print(num_val, len(data["data"]))
        return

@tasks.loop(seconds=10)
async def get_notice():
    global num_notice
    global Noticechannel
    global Logchannel
    await bot.wait_until_ready()
    try:
        response = requests.get(url + "/notice")
        data = json.loads(response.text)
    except:
        mes = "水やり通知のメッセージの取得に失敗しました. apiサーバーが起動しているか確認してください."
        await Logchannel.send(makelog("Error", mes))
        return
    if num_notice == len(data["data"]):
        return
    else:
        num_notice += 1
        try:
            if data["data"][num_notice - 1]["notice"] == 1:
                await Noticechannel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やり開始```")
            elif data["data"][num_notice - 1]["notice"] == 0:
                await Noticechannel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やり終了```")
            else:
                await Noticechannel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やりtimeout```")
        except:
            mes = "get_notice, noticeがリセットされました.データベースがリセットされました."
            print(f"Error: {mes}")
            await Logchannel.send(makelog("Error", mes))
            num_notice = len(data["data"])

@tasks.loop(seconds=60)
# 指定時間に水やり指示を送信
async def post_flag():
    global Valchannel
    global Logchannel
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
                    await Valchannel.send(f"Error: 水やり指示の送信に失敗しました")
                    await Logchannel.send(makelog("Error", "水やり指示の送信に失敗しました"))
                    return
                await Valchannel.send(f"水やり指示を出しました")
                await Logchannel.send(makelog("Info", "水やり指示を出しました"))
                return

# Botを起動
bot.run(token)
