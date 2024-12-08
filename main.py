import asyncio
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta
from uuid import uuid4
import requests

import websockets

from modules import content_format



file_path: str = os.path.dirname(sys.argv[0])
if file_path == "":
    file_path = "."

def setup():
    config = {}
    config["instance"] = input("Instance: ")
    config["token"] = input("Token: ")
    config["name_len"] = 25
    config["content_len"] = 1000
    config["line_len"] = 50
    config["time_shift"] = 9
    json.dump(config, open(file_path + "/config.json", "w"))


def pick_data(res, config):
    # 名前の抽出
    name = content_format.get_name(res, config)
    uid = content_format.get_uid(res)
    host_name = content_format.get_instance_name(res)

    # 時間の抽出
    time = content_format.get_time(res, config)

    # 内容の抽出
    cw, content = content_format.get_content(res)

    return {
        "name": name,
        "uid": uid,
        "host_name": host_name,
        "time": time,
        "cw": cw,
        "content": content,
    }

def insert_space(indent_len):
    return " " * indent_len



def print_data(data, res, config, indent=""):
    INDENT_SPACE = ": "  # インデントがあった際に挿入するスペース

    # インデントがあった際はそのインデントとスペース、名前とuidを表示
    print((indent + INDENT_SPACE if indent else "") + data["name"], " | ", data["uid"])
    if indent != "":  # インデントがあった際はindent_lenにインデント自体の長さとスペースの長さを挿入
        indent_len: int = len(indent) + len(INDENT_SPACE)
    else:
        indent_len = 0  # インデントがない場合は0
    print(insert_space(indent_len)  + data["time"], " | ", data["host_name"])  # 時間とインスタンス名を表示
    print(insert_space(indent_len)  + "-" * (config["line_len"] - indent_len))  # ラインを表示
    if data["cw"] is not None:  # CWがある場合は表示
        print(insert_space(indent_len)  + data["cw"])  # CWの概要
        print(insert_space(indent_len)  + "~" * config["line_len"])  # ラインを表示
    if len(data["content"]) > config["content_len"]:  # コンテンツが長い場合は省略を行う
        remain_char = len(data["content"]) - config["content_len"]  # 残りの文字数を計算
        data["content"] = data["content"][: config["content_len"]]  # 文字数を制限
        data["content"] += "..."  # 省略記号を追加
        data["content"] += "\n(" + str(remain_char) + " letters left)"  # 残りの文字数を表示
    for row in data["content"].split("\n"):  #  改行記号ごとに分割して表示
        print(insert_space(indent_len)  + row)  # コンテンツを表示
    if len(res["fileIds"]) > 0:  # 添付ファイルがある場合は表示
        if len(res["fileIds"]) > 1:  # 複数の場合はfiles、単数の場合はfile
            print(insert_space(indent_len)  + f"({len(res['fileIds'])} files)")
        else:
            print(insert_space(indent_len)  + f"({len(res['fileIds'])} file)")
    if res.get("poll") is not None:  # 投票がある場合は表示
        print(insert_space(indent_len)  + "(Vote)")


async def main():
    config = json.load(open(file_path + "/config.json", "r"))
    MODE_LIST = {
        "h": "homeTimeline",
        "l": "localTimeline",
        "s": "hybridTimeline",
        "g": "globalTimeline",
    }
    # ユーザー情報を取得して送信
    USER_INFO = requests.post(
        "https://" + config["instance"] + "/api/i", json={"i": config["token"]}
    )
    if USER_INFO.status_code != 200:
        print("Failed to get user info")
        return
    JSON_DATA = USER_INFO.json()
    print(f"logged in as {JSON_DATA['name'  ]}")
    print(f"@{JSON_DATA['username']}@{config['instance']}")
    print("-" * 30)
    while True:
        try:
            mode = MODE_LIST[input("Mode: ")]
            break
        except KeyError:
            print("Invalid mode")
            print("params: h, l, s, g")
    while True:
        try:
            id = str(uuid4())
            async with websockets.connect(
                f"wss://{config['instance']}/streaming?i={config['token']}"
            ) as ws:
                await ws.send(
                    json.dumps({"type": "connect", "body": {"channel": mode, "id": id}})
                )
                print("connected")
                print("=" * config["line_len"])
                while True:
                    res = json.loads(await ws.recv())
                    if res["body"].get("id") == id:
                        res = res["body"]["body"]
                        # 情報の抽出
                        data = pick_data(res, config)
                        print_data(data, res, config)

                        if res["renoteId"] is not None:
                            print("-" * config["line_len"])
                            rn_data = pick_data(res["renote"], config)
                            print_data(rn_data, res["renote"], config, "rn")
                        if res["replyId"] is not None:
                            print("-" * config["line_len"])
                            rn_data = pick_data(res["reply"], config)
                            print_data(rn_data, res["reply"], config, "rp")
                        print("=" * config["line_len"])

        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
        ):
            print("Connection closed")
            print("Reconnecting...")
            print("-" * 30)


if __name__ == "__main__":
    if not os.path.exists( file_path + "/config.json"):
        setup()
    asyncio.run(main())
