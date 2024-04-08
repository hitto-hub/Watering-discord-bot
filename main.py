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
        # Logchannelを取得
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
        # supply_countを取得
        try:
            self.supply_count = int(json.loads(requests.get(url + "/supply/count").text)["num_results"])
            print(makelog("Info", f"init: supply_count: {self.supply_count}"))
        except:
            print(makelog("Error", "supply_countの取得に失敗しました"))
            self.supply_count = None
        # wetness_value_count, temperature_value_count, humidity_value_countを取得
        try:
            self.wetness_value_count = int(json.loads(requests.get(url + "/wetness_value/count").text)["num_results"])
            print(makelog("Info", f"init: wetness_value_count: {self.wetness_value_count}"))
        except:
            print(makelog("Error", "wetness_value_countの取得に失敗しました"))
            self.wetness_value_count = None
        try:
            self.temperature_value_count = int(json.loads(requests.get(url + "/temperature_value/count").text)["num_results"])
            print(makelog("Info", f"init: temperature_value_count: {self.temperature_value_count}"))
        except:
            print(makelog("Error", "temperature_value_countの取得に失敗しました"))
            self.temperature_value_count = None
        try:
            self.humidity_value_count = int(json.loads(requests.get(url + "/humidity_value/count").text)["num_results"])
            print(makelog("Info", f"init: humidity_value_count: {self.humidity_value_count}"))
        except:
            print(makelog("Error", "humidity_value_countの取得に失敗しました"))
            self.humidity_value_count = None
    def set_Logchannel(self, channel):
        self.Logchannel = channel
    def get_Logchannel(self):
        return self.Logchannel
    def set_supply_count(self, count):
        self.supply_count = count
    def get_supply_count(self):
        return self.supply_count
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

def get_name_to_address(name: str):
    response = requests.get(url + "/addresses/" + name)
    if response.status_code != 200:
        return None, "addressの取得に失敗しました"
    if response.json()["status"] == False:
        return None, response.json()["message"]
    elif response.json()["status"] == True:
        return response.json()["address"], response.json()["message"]
    else:
        return None, "予期せぬエラーが発生しました"

# 起動時に自動的に動くメソッド
@bot.event
async def on_ready():
    global w
    w = watering_data()
    Logchannel = w.get_Logchannel()
    try:
        response = requests.get(url)
    except:
        print(makelog("Error", "apiサーバーが起動していません"))
        await Logchannel.send(makelog("Error", "apiサーバーが起動していません"))
        return
    # 定期実行を開始
    monitor_supply.start()
    # 起動メッセージをLogchannelにメッセージを送信
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
    # global w
    Logchannel = w.get_Logchannel()
    data = {"instruction": 1}
    # nameからaddressを取得
    address, mes = get_name_to_address(name)
    if address is None: # エラー時
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))
        return
    instructions_url = url + "/instructions/" + str(address)
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
    # global w
    Logchannel = w.get_Logchannel()
    # nameからaddressを取得
    address, mes = get_name_to_address(name)
    if address is None: # エラー時
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))
        return
    
    watering_regular_url = url + "/watering_regular/" + str(address)
    data = {
            "time_hour": settime.split(":")[0],
            "time_minutes": settime.split(":")[1],
            "weekday": weekday
            }
    response = requests.post(watering_regular_url, json=data)
    if response.status_code != 200:
        mes = "水やり予約の追加に失敗しました"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))
        return
    if response.json()["status"] == False:
        mes = response.json()["message"]
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))
    elif response.json()["status"] == True:
        mes = f"水やり予約を追加しました。{settime} {weekday}"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Info", mes))
    else:
        # 予期せぬエラー
        mes = "水やり予約の追加に失敗しました. 予期せぬエラーが発生しました."
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))

# /wateringregular remove time weekday
# time, weekdayを指定して水やり予約を削除できる
@wateringregular.command(
    name="remove",
    description="水やり予約を削除します"
)
async def remove(ctx: discord.ApplicationContext,
                name: discord.Option(str, "名前を入力してください", name="name"),
                settime: discord.Option(str, "時間\"HH:MM\"を入力してください", name="time"),
                weekday: discord.Option(str, "曜日を入力してください", name="weekday", choices=["mon", "tue", "wed", "thu", "fri", "sat", "sun", "all"])):
    # global w
    Logchannel = w.get_Logchannel()
    # nameからaddressを取得
    address, mes = get_name_to_address(name)
    if address is None: # エラー時
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))
        return
    watering_regular_url = url + "/watering_regular/" + str(address)
    data = {
            "time_hour": settime.split(":")[0],
            "time_minutes": settime.split(":")[1],
            "weekday": weekday
            }
    response = requests.delete(watering_regular_url, json=data)
    if response.status_code != 200:
        mes = "水やり予約の削除に失敗しました"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))
        return
    if response.json()["status"] == False:
        mes = response.json()["message"]
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))
    elif response.json()["status"] == True:
        mes = f"水やり予約を削除しました。{settime} {weekday}"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Info", mes))
    else:
        # 予期せぬエラー
        mes = "水やり予約の削除に失敗しました. 予期せぬエラーが発生しました."
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))

# /wateringregular list
# 水やり予約一覧を表示
@wateringregular.command(
    name="list",
    description="水やり予約一覧を表示します"
)
async def list(ctx: discord.ApplicationContext):
    Logchannel = w.get_Logchannel()
    watering_regular_url = url + "/watering_regular"
    response = requests.get(watering_regular_url)
    if response.status_code != 200:
        mes = "水やり予約の取得に失敗しました"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))
        return
    if response.json()["status"] == False:
        mes = response.json()["message"]
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))
    elif response.json()["status"] == True:
        mes = "水やり予約一覧\n"
        for entry in response.json()["data"]:
            mes += f"{entry['name']} : {entry['time_hour']}:{entry['time_minutes']} {entry['weekday']}\n"
        await ctx.respond(mes)
        await Logchannel.send(makelog("Info", mes))
    else:
        # 予期せぬエラー
        mes = "水やり予約の取得に失敗しました. 予期せぬエラーが発生しました."
        await ctx.respond(mes)
        await Logchannel.send(makelog("Error", mes))

@tasks.loop(seconds=10)
async def monitor_supply():
    Logchannel = w.get_Logchannel()
    response = requests.get(url + "/supply/count")
    if response.status_code != 200:
        mes = "fail to get_supply_count"
        await Logchannel.send(makelog("Error", mes))
        return
    if w.get_supply_count() < int(json.loads(response.text)["num_results"]): # 新しいデータがある場合
        w.set_supply_count(w.get_supply_count() + 1)
        supply_count = w.get_supply_count()
        response = requests.get(url + "/supply")
        if response.status_code != 200:
            mes = "fail to get_supply"
            await Logchannel.send(makelog("Error", mes))
            return
        data = json.loads(response.text)
        if response.json()["status"] == False:
            mes = response.json()["message"]
            await Logchannel.send(makelog("Error", mes))
            return
        elif response.json()["status"] == True:
            # timestamp
            mes_timestamp = data['data'][supply_count - 1]['timestamp']
            # address
            mes_address = data['data'][supply_count - 1]['address']
            # name
            try:
                response = requests.get(url + "/addresses/" + mes_address)
            except: # 通信エラー時
                mes_name = "None"
                mes = "fail to get_name"
                await Logchannel.send(makelog("Error", mes))
            if response.status_code != 200: # 通信エラー時
                mes_name = "None"
                mes = "fail to get_name"
                await Logchannel.send(makelog("Error", mes))
            if response.json()["status"] == True:
                mes_name = response.json()["name"]
            else:
                mes_name = "名前が取得できませんでした.databaseerror"
            # supplyの最新データを表示
            type = {data['data'][supply_count - 1]['type']}
            if type == 0:
                mes_type = "水やり終了"
            elif type == 1:
                mes_type = "水やり開始"
            elif type == 2:
                mes_type = "水やりが正常に終了しませんでした"
            else:
                mes_type = "不明なデータです"
            mes = f"timestamp: {mes_timestamp}, address: {mes_address},neme: {mes_name}, type: {mes_type}"
            print(makelog("Info", mes))
            await Logchannel.send(makelog("Info", mes))
        else:
            mes = "予期せぬエラーが発生しました"
            await Logchannel.send(makelog("Error", mes))
            return

# Botを起動
bot.run(token)
