import websockets
import json
import os
from uuid import uuid4
import asyncio
from datetime import datetime
import re
import unicodedata


def setup():
    config = {}
    config["instance"] = input("Instance: ")
    config["token"] = input("Token: ")
    config["name_len"] = 25
    config["content_len"] = 1000
    config["line_len"] = 50
    json.dump(config, open("config.json", "w"))


def pick_data(res, config):
    cat_re_1 = re.compile(r"(na)", re.IGNORECASE)
    cat_re_2 = re.compile(r"(な)", re.IGNORECASE)
    cat_re_3 = re.compile(r"(ナ)", re.IGNORECASE)
    count = 0
    name = res["user"]["name"] if res["user"]["name"] is not None else res["user"]["username"]
    for char in name:
        if unicodedata.east_asian_width(char) in ("F", "W", "A"):
            count += 2
        else:
            count += 1
    if count > config["name_len"]:
        name = name[: (count - config["name_len"]) - 3] + "..."
        count = count + 3
    name += " " * (config["name_len"] - count)
    uid = "@" + res["user"]["username"]
    # ホストの抽出
    if res["user"]["host"] is not None:
        uid += "@" + res["user"]["host"]
        host_name = res["user"]["instance"]["name"]
    else:
        host_name = "This instance"

    # 時間の抽出
    time = datetime.strftime(
        datetime.fromisoformat(res["createdAt"]),
        "%Y-%m-%dT%H:%M:%S",
    ).ljust(config["name_len"])

    # 内容の抽出
    cw = res["cw"]
    content = res["text"]
    if content is not None:
        # cat
        if res["user"]["isCat"]:
            content = cat_re_1.sub("nya", content)
            content = cat_re_2.sub("にゃ", content)
            content = cat_re_3.sub("ニャ", content)
    else:
        content = "No content"
    return {"name": name, "uid": uid, "host_name": host_name, "time": time, "cw": cw, "content": content}


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
        data["content"] = data["content"][:config["content_len"]]
        data["content"] += "..."
        data["content"] += "\n(" + str(remain_char) + " letters left)"
    for row in data["content"].split("\n"):
        print(" " * indent + row)
    if len(res["fileIds"]) > 0:
        print(" " * indent + f"({len(res["fileIds"])} file(s))")
    if res.get("poll") is not None:
        print(" " * indent + "(Vote)")


async def main():
    config = json.load(open("config.json", "r"))
    mode_list = {
        "h": "homeTimeline",
        "l": "localTimeline",
        "s": "hybridTimeline",
        "g": "globalTimeline",
    }
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
                    if res["body"]["id"] == id:
                        res = res["body"]["body"]
                        # 情報の抽出
                        data = pick_data(res, config)
                        print_data(data, res, config)

                        if res["renoteId"] is not None:
                            print("-"*config["line_len"])
                            rn_data = pick_data(res["renote"], config)
                            print_data(rn_data, res["renote"], config, "rn")
                        if res["replyId"] is not None:
                            print("-"*config["line_len"])
                            rn_data = pick_data(res["reply"], config)
                            print_data(rn_data, res["reply"], config, "rp")
                        print("=" * config["line_len"])

        except websockets.exceptions.ConnectionClosedError:
            print("Connection closed")
            print("Reconnecting...")
            print("-" * 30)


if __name__ == "__main__":
    if not os.path.exists("config.json"):
        setup()
    asyncio.run(main())
