import re

def nyaize(content):
    cat_re_1 = re.compile(r"(na)", re.IGNORECASE)
    cat_re_2 = re.compile(r"(な)", re.IGNORECASE)
    cat_re_3 = re.compile(r"(ナ)", re.IGNORECASE)

    content = cat_re_1.sub("nya", content)
    content = cat_re_2.sub("にゃ", content)
    content = cat_re_3.sub("ニャ", content)

    return content
