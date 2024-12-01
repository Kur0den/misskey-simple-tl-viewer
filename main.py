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
    time = datetime.strftime(
        datetime.fromisoformat(res["createdAt"][:-1])
        + timedelta(hours=config["time_shift"]),
        "%Y-%m-%dT%H:%M:%S",
    ).ljust(config["name_len"])

    # 内容の抽出
    cw = res["cw"]
    content = res["text"]
    if content is not None:
        # isCat
        if res["user"]["isCat"]:
            content = content_format.nyaize(content)

    else:
        content = "No content"
    return {
        "name": name,
        "uid": uid,
        "host_name": host_name,
        "time": time,
        "cw": cw,
        "content": content,
    }


def print_data(data, res, config, indent=""):
    print((indent + ": " if indent else "") + data["name"], " | ", data["uid"])
    if indent != "":
        indent = len(indent) + 2
    else:
        indent = 0
    print(" " * indent + data["time"], " | ", data["host_name"])
    print(" " * indent + "-" * (config["line_len"] - indent))
    if data["cw"] is not None:
        print(" " * indent + data["cw"])
        print(" " * indent + "~" * config["line_len"])
    if len(data["content"]) > config["content_len"]:
        remain_char = len(data["content"]) - config["content_len"]
        data["content"] = data["content"][: config["content_len"]]
        data["content"] += "..."
        data["content"] += "\n(" + str(remain_char) + " letters left)"
    for row in data["content"].split("\n"):
        print(" " * indent + row)
    if len(res["fileIds"]) > 0:
        print(" " * indent + f"({len(res['fileIds'])} file(s))")
    if res.get("poll") is not None:
        print(" " * indent + "(Vote)")


async def main():
    config = json.load(open(file_path + "/config.json", "r"))
    mode_list = {
        "h": "homeTimeline",
        "l": "localTimeline",
        "s": "hybridTimeline",
        "g": "globalTimeline",
    }
    # ユーザー情報を取得して送信
    user_info = requests.post(
        "https://" + config["instance"] + "/api/i", json={"i": config["token"]}
    )
    if user_info.status_code != 200:
        print("Failed to get user info")
        return
    print(f"logged in as {user_info.json()['name']}")
    print(f"@{user_info.json()['username']}@{config['instance']}")
    print("-" * 30)
    while True:
        try:
            mode = mode_list[input("Mode: ")]
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
