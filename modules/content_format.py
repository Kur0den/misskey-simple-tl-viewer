import re
import unicodedata
from datetime import datetime, timedelta


def name_counter(name):
    count = 0
    for char in name:
        match unicodedata.east_asian_width(char):
            case "W" | "F":  # 全角文字等
                count += 2  # 2文字分増やす
            case "a":  # 曖昧な文字
                pass  # 何もしない
            case _:  # その他
                count += 1  # 1文字分増やす
    return count


def name_formatter(name, name_len, config):
    TARGET_LEN = config["name_len"] - len("... ")  # 設定値から...の分を引く
    for char in name[::-1]:  #  文字列を逆順にして文字数を減らしていく
        match unicodedata.east_asian_width(char):
            case "W" | "F":  # 全角文字
                name_len -= 2  # 2文字分減らす
                name = name[:-1]
            case "a":  # 曖昧な文字
                pass  # 何もしない
            case _:  # その他
                name_len -= 1  # 1文字分減らす
                name = name[:-1]
        if name_len <= TARGET_LEN:  # 設定値以下になったらbreak
            break
    format_name = name + "... "  # 省略を示す...を追加
    return format_name


def get_name(res, config):
    # ユーザー名を取得
    # ユーザー名がない場合はハンドルを取得
    name = (
        res["user"]["name"]
        if res["user"]["name"] is not None
        else res["user"]["username"]
    )
    # ここでのcountは文字数
    count = name_counter(name)

    # 文字数が設定値を超えている場合は省略
    if (config["name_len"] - 1) - count < 0:
        format_name = name_formatter(name, count, config)
    else:  # 超えていない場合はnameをそのまま
        format_name = name
    # 設定値に満たない場合はスペースで埋める
    format_name = format_name + " " * (config["name_len"] - name_counter(format_name))
    return format_name


def get_uid(res):
    uid = "@" + res["user"]["username"]
    if res["user"]["host"] is not None:
        uid += "@" + res["user"]["host"]
    return uid


def get_instance_name(res):  # -> Any | Literal['No instance name']:
    if res["user"]["host"] is not None:
        if res["user"]["instance"]["name"] is not None:
            return res["user"]["instance"]["name"]
        else:
            return "No instance name"
    else:
        return "Local"


def get_time(res, config):
    return datetime.strftime(
        datetime.fromisoformat(res["createdAt"][:-1])  # isoformatの最後のZを削除してdatetimeに変換
        + timedelta(hours=config["time_shift"]),  # タイムゾーンの補正
        "%Y-%m-%dT%H:%M:%S",  # 文字列に変換
    ).ljust(config["name_len"])  # 文字数を調整

def get_content(res):
    cw = res["cw"]  # Content Warning
    content = res["text"]  # 本文
    if content is not None:  # 本文がある場合
        # isCat
        if res["user"]["isCat"]:
            content = nyaize(content)  # にゃいず
    else:
        content = "[No content]"  # 本文がない場合
    return cw, content


def nyaize(content):
    cat_re_1 = re.compile(r"(na)", re.IGNORECASE)
    cat_re_2 = re.compile(r"(な)", re.IGNORECASE)
    cat_re_3 = re.compile(r"(ナ)", re.IGNORECASE)

    content = cat_re_1.sub("nya", content)
    content = cat_re_2.sub("にゃ", content)
    content = cat_re_3.sub("ニャ", content)

    return content
