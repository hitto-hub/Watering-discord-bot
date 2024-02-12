# json file: data.json
# {
#   "data": [
#     {
#       "id": 1,
#       "timestamp": "Fri, 09 Feb 2024 04:09:37 GMT",
#       "val": 334
#     },
#     {
#       "id": 2,
#       "timestamp": "Fri, 09 Feb 2024 04:12:46 GMT",
#       "val": 334
#     },
#     {
#       "id": 3,
#       "timestamp": "Fri, 09 Feb 2024 08:08:38 GMT",
#       "val": 31111
#     }
#   ]
# }

import json
Message = []

data = json.load(open("data.json", "r"))
print("--------------------")
print(data)
print("--------------------")
print(data["data"])
print("--------------------")
print(data["data"][0])
print("--------------------")
for entry in data["data"]:
    mes = f"id: {entry['id']}, timestamp: {entry['timestamp']}, val: {entry['val']}"
    print(mes)
print("--------------------")
messs = {'id': 1, 'timestamp': 'Fri, 09 Feb 2024 04:09:37 GMT', 'val': 334}
for key, value in messs.items():
    print(f"{key}: {value}")
  