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
url = str(os.getenv("API_URL")) # httpsではpost出来ない例あり 関連)https://community.cloudflare.com/t/cloudflared-tunnel-receives-post-request-as-get/581874
url = "http://localhost:5050/api" # ローカルでのテスト用
Logchannelid = str(os.getenv("LOG_CHANNEL_ID"))

def makelog(header: str, message: str) -> str:
    return f'[{time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())} : {header}] {message}'

# Botの大元となるオブジェクトを生成する
bot = discord.Bot(
        intents=discord.Intents.all(),  # 全てのインテンツを利用できるようにする
        activity=discord.Game("💧"),  # "〇〇をプレイ中"の"〇〇"を設定,
)

class watering_data:
    def __init__(self):
        try:
            # メッセージを送信するchannelを取得
            for channel in bot.get_all_channels():
                if int(channel.id) == int(Logchannelid):
                    self.Logchannel = channel # Logchannelをセット
                    print(makelog("Info", f"init: Logchannel:{self.Logchannel}"))
                    break
            if self.Logchannel is None:
                print(makelog("Error", "Logchannelが見つかりませんでした"))
                exit()
        except:
            print(makelog("Error", "Logchannelの取得に失敗しました"))
            exit()
        try:
            self.wetness_value_count = int(json.loads(requests.get(url + "/wetness_value/count").text)["num_results"])
            print(makelog("Info", f"init: wetness_value_count: {self.wetness_value_count}"))
        except:
            print(makelog("Error", "wetness_value_countの取得に失敗しました"))
            self.wetness_value_count = 0
        try:
            self.temperature_value_count = int(json.loads(requests.get(url + "/temperature_value/count").text)["num_results"])
            print(makelog("Info", f"init: temperature_value_count: {self.temperature_value_count}"))
        except:
            print("Error: temperature_value_countの取得に失敗しました")
            self.temperature_value_count = 0
        try:
            self.humidity_value_count = int(json.loads(requests.get(url + "/humidity_value/count").text)["num_results"])
            print(makelog("Info", f"init: humidity_value_count: {self.humidity_value_count}"))
        except:
            print("Error: humidity_value_countの取得に失敗しました")
            self.humidity_value_count = 0
    def set_Logchannel(self, channel):
        self.Logchannel = channel
    def get_Logchannel(self):
        return self.Logchannel
    def set_wetness_value_count(self, count):
        self.wetness_value_count = count
    def get_wetness_value_count(self):
        return self.wetness_value_count
    def set_temperature_value_count(self, count):
        self.temperature_value_count = count
    def get_temperature_value_count(self):
        return self.temperature_value_count
    def set_humidity_value_count(self, count):
        self.humidity_value_count = count
    def get_humidity_value_count(self):
        return self.humidity_value_count

# wateringregularグループを作成
wateringregular = bot.create_group(name="wateringregular", description="水やり予約関連")

def get_name_to_address(name: str) -> int:
    return json.loads(requests.get(url + "/addresses/" + name).text)["address"]

# 起動時に自動的に動くメソッド
@bot.event
async def on_ready():
    w = watering_data()
    # 定期実行を開始
    # get_val.start()
    # get_notice.start()
    # post_flag.start()
    # 起動メッセージをLogchannelにメッセージを送信
    Logchannel = w.get_Logchannel()
    mes = "正常に起動しました"
    print(makelog("Info", mes))
    await Logchannel.send(makelog("Info", mes))

# pingコマンドを実装
@bot.command(name="ping", description="pingを返します")
async def ping(ctx: discord.ApplicationContext):
    mes = f"ping from {ctx.author.mention}"
    print(makelog("Info", mes))
    await ctx.respond(f"pong to {ctx.author.mention}")

# /wateringコマンドを実装
# このコマンドを実行すると、apiサーバーに水やり指示を送信する
@bot.command(name="watering", description="水やりを開始します")
async def watering(ctx: discord.ApplicationContext,
                    name: discord.Option(str, "名前を入力してください", name="name")):
    w = watering_data()
    Logchannel = w.get_Logchannel()
    data = {"instruction": 1}
    instructions_url = url + "/instructions/" + str(get_name_to_address(name))
    try:
        response = requests.post(instructions_url, json=data)
    except: # 通信エラー時
        mes = "水やり指示の送信に失敗しました, apiサーバーが起動しているか確認してください"
        await ctx.respond(f"Error: {mes}")
        await Logchannel.send(makelog("Error", mes))
        return
    mes = "水やり指示を出しました"
    await ctx.respond(f"{mes}")
    await Logchannel.send(makelog("Info", mes))

# /wateringregularコマンドを実装
# /wateringregular add time weekday
# time, weekdayを指定して水やり予約を追加できる
@wateringregular.command(
    name="add",
    description="水やり予約を追加します"
)
async def add(ctx: discord.ApplicationContext,
                name: discord.Option(str, "名前を入力してください", name="name"),
                settime: discord.Option(str, "時間\"HH:MM\"を入力してください", name="time"),
                weekday: discord.Option(str, "曜日を入力してください", name="weekday", choices=["mon", "tue", "wed", "thu", "fri", "sat", "sun", "all"])):
    w = watering_data()
    watering_regular_url = url + "/watering_regular/" + str(get_name_to_address(name))
    if settime + " " + weekday in watering_time:
        mes = "水やり予約が重複しています"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))
    else:
        watering_time.add(settime + " " + weekday)
        mes = f"水やり予約を追加しました。{watering_time}"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Info", mes))

# /wateringregular remove time weekday
# time, weekdayを指定して水やり予約を削除できる
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

# /wateringregular list
# 水やり予約一覧を表示
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

# # 10秒ごとにchannelidにメッセージを送信
# # ToDo: 値の取得、表示方法を改善
# @tasks.loop(seconds=10)
# async def get_val():
#     global num_val
#     global Valchannel
#     global Logchannel
#     # 起動するまで待つ
#     await bot.wait_until_ready()
#     # リクエストを送信
#     try:
#         response = requests.get(url + "/val")
#         data = json.loads(response.text)
#     except: # 通信エラー時
#         mes = "水分量のメッセージの取得に失敗しました. apiサーバーが起動しているか確認してください."
#         await Logchannel.send(makelog("Error", mes))
#         return
#     for entry in data["data"]:
#         # Message[id]が存在しない場合、Message[id]に格納
#         if num_val < int(entry['id']):
#             num_val = int(entry['id'])
#             mes = f"{entry['timestamp']} : {entry['val']}"
#             await Valchannel.send(mes)
#     # print(num_val, len(data["data"]))
#     if num_val > len(data["data"]):
#         num_val = int(json.loads(requests.get(url + "/val").text)["num_results"])
#         mes = "get_val, valがリセットされました.データベースがリセットされました."
#         print(f"Error: {mes}")
#         await Logchannel.send(makelog("Error", mes))
#         # print(num_val, len(data["data"]))
#         return

# @tasks.loop(seconds=10)
# async def get_notice():
#     global num_notice
#     global Noticechannel
#     global Logchannel
#     await bot.wait_until_ready()
#     try:
#         response = requests.get(url + "/notice")
#         data = json.loads(response.text)
#     except: # 通信エラー時
#         mes = "水やり通知のメッセージの取得に失敗しました. apiサーバーが起動しているか確認してください."
#         await Logchannel.send(makelog("Error", mes))
#         return
#     if num_notice == len(data["data"]):
#         return
#     else:
#         num_notice += 1
#         try:
#             if data["data"][num_notice - 1]["notice"] == 1:
#                 await Logchannel.send(makelog("Info", f"{data['data'][num_notice - 1]['timestamp']} : 水やり開始"))
#                 await Noticechannel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やり開始```")
#             elif data["data"][num_notice - 1]["notice"] == 0:
#                 await Logchannel.send(makelog("Info", f"{data['data'][num_notice - 1]['timestamp']} : 水やり終了"))
#                 await Noticechannel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やり終了```")
#             else:
#                 await Logchannel.send(makelog("Info", f"{data['data'][num_notice - 1]['timestamp']} : 水やりtimeout"))
#                 await Noticechannel.send(f"```{data['data'][num_notice - 1]['timestamp']} : 水やりtimeout```")
#         except:
#             mes = "get_notice, noticeがリセットされました.データベースがリセットされました."
#             print(f"Error: {mes}")
#             await Logchannel.send(makelog("Error", mes))
#             num_notice = len(data["data"])

# @tasks.loop(seconds=60)
# # 指定時間に水やり指示を送信
# async def post_flag():
#     global Valchannel
#     global Logchannel
#     # @bot.event on_readyが呼ばれるまで待つ
#     await bot.wait_until_ready()
#     # 時間を取得
#     now = time.strftime("%H:%M", time.localtime())
#     # 曜日を取得
#     weekday = time.strftime("%a", time.localtime()).lower()
#     print(now, weekday)
#     # 水やり予約がある場合
#     if len(watering_time) > 0:
#         for watering_time_slot in watering_time:
#             if watering_time_slot.split(" ")[0] == now and (watering_time_slot.split(" ")[1] == weekday or watering_time_slot.split(" ")[1] == "all"):
#                 data = {"flag": 1}
#                 flag_url = url + "/flag"
#                 try:
#                     response = requests.post(flag_url, json=data)
#                 except:
#                     mes = "予約された水やり指示の送信に失敗しました"
#                     await Valchannel.send(f"Error: {mes}")
#                     await Logchannel.send(makelog("Error", mes))
#                     return
#                 mes = "予約された水やり指示を出しました"
#                 await Valchannel.send(mes)
#                 await Logchannel.send(makelog("Info", mes))
#                 return

# Botを起動
bot.run(token)
