import requests
import time
from datetime import datetime, timedelta

# ここにtokne入れると動く
headers = {'Authorization': 'Bearer XXXXX'}

ignore_channel = ["XXXX"]


def get_channel_list():
    params = {}
    params.update(limit=1000)
    r = requests.get("https://slack.com/api/conversations.list", params=params, headers=headers)
    json = r.json()

    # PublicChannelのIDを格納
    channels = []

    for channel in json["channels"]:
        if channel["id"] not in ignore_channel:
            channels.append(channel["id"])
        else:
            print("ignore_channel : " + channel["name"])

    print("パブリックチャンネル数: ", len(json["channels"]))
    return channels


def get_conversations_history(channel, param):
    param.update(limit=1000, channel=channel)
    r = requests.get("https://slack.com/api/conversations.history", params=param, headers=headers)
    json = r.json()
    return json


def count_emoji(channels):
    # 絵文字を格納
    emojis = {}

    oldest = (datetime.now() - timedelta(days=90)).timestamp()
    param = {}
    param.update(oldest=oldest)

    for channel in channels:
        result = get_conversations_history(channel, param)
        messages = result["messages"]
        if len(messages) == 0:
            continue

        has_more = result["has_more"]
        cursor = ""
        if "response_metadata" in result:
            cursor = result["response_metadata"]["next_cursor"]

        while has_more:
            new_param = {}
            new_param.update(limit=1000, channel=channel, oldest=oldest, latest=messages[-1]["ts"],
                             cursor=cursor)
            result = get_conversations_history(channel, new_param)
            messages += result["messages"]
            has_more = result["has_more"]
            if "response_metadata" in result:
                cursor = result["response_metadata"]["next_cursor"]

        # チャンネルのメッセージ分（MAX1000）
        for message in messages:
            if "reactions" in message:
                # ついたリアクションの種類分
                for reaction in message["reactions"]:
                    # 集計リストに追加
                    if reaction["name"] in emojis:
                        emojis[reaction["name"]] += reaction["count"]
                    else:
                        emojis[reaction["name"]] = reaction["count"]

        # 制限対策
        time.sleep(1)

    print("絵文字数: ", len(emojis))
    return emojis


def sort_30(emojis):
    emojis_sorted = sorted(emojis.items(), key=lambda x: x[1], reverse=True)[:30]

    return emojis_sorted


if __name__ == '__main__':
    channel = get_channel_list()
    emojis = count_emoji(channel)

    emojis_sorted = sort_30(emojis)
    # ファイルに出力
    f = open('result.txt', 'w')
    for data, i in emojis_sorted:
        f.write(str(i + 1) + "位 :" + str(data).replace("'", ":") + "回\n")
    f.close()
