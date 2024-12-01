import re

def nyaize(content):
    cat_re_1 = re.compile(r"(na)", re.IGNORECASE)
    cat_re_2 = re.compile(r"(な)", re.IGNORECASE)
    cat_re_3 = re.compile(r"(ナ)", re.IGNORECASE)

    content = cat_re_1.sub("nya", content)
    content = cat_re_2.sub("にゃ", content)
    content = cat_re_3.sub("ニャ", content)

    return content


def get_name(res, config):
    count = 0
    count = len(res["user"]["username"])
    name = res["user"]["username"]
    if count > config["name_len"]:
        name = name[: (count - config["name_len"]) - 3] + "..."
        count = count + 3
    name += " " * (config["name_len"] - count)
    return name

def get_uid(res):
    uid = "@" + res["user"]["username"]
    if res["user"]["host"] is not None:
        uid += "@" + res["user"]["host"]
    return uid

def get_instance_name(res):# -> Any | Literal['No instance name']:
    if res["user"]["host"] is not None:
        if res["user"]["instance"]["name"] is not None:
            return res["user"]["instance"]["name"]
        else:
            return "No instance name"
    else:
        return "Local"
