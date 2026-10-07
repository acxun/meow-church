#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用【纯 Meow】生成一个计算质数的程序（.docx）。

Meow 没有算术/条件/循环，但它本质是 lambda 演算，所以这里用邱奇数 + 邱奇布尔
把 prime(n) 编码出来。Meow 是严格求值且 lambda 参数个数精确，所以：
  * 需要“返回值”时用嵌套 lambda（不做柯里化部分应用）
  * 需要惰性 if 时用 thunk：IF c t f = (c t f) FORCE

记号（生成器内部 DSL）：
  I(name)            -> 一个用户标识符（名字就是排版）
  G(*items)          -> 一对斜体 Meow（括号），内部是表达式列表
  LAM(params,*body)  -> (lambda (params...) body...)
  RICH(text)         -> 一对下划线 Meow（富文本/字符串字面量）
  LET/I('x')/value   -> 顶层 let 语句
"""
import os
import zipfile
import colorsys

# ---------- 内置 token 样式（必须与 org.glavo.meow 完全一致） ---------------
STYLE = {
    "let":     dict(color="00B0F0", highlight="lightGray"),
    "lambda":  dict(color="00B050", highlight="lightGray"),
    "integer": dict(color="000000", highlight="lightGray"),
    "print":   dict(color="EE0000", highlight="yellow"),
}

MEOW = "Meow"


def _distinct_colors(n, s, v, seed_hue=0.0):
    cols, seen, h = [], set(), seed_hue
    while len(cols) < n:
        h = (h + 137.508) % 360.0
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
        c = "%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))
        if c not in seen:
            seen.add(c)
            cols.append(c)
    return cols


# 用户标识符：每个“名字”一种唯一颜色（继续按需生成）
_id_colors = {}
_id_palette = _distinct_colors(200, 0.80, 0.72)


def id_color(name):
    if name not in _id_colors:
        _id_colors[name] = _id_palette[len(_id_colors)]
    return _id_colors[name]


# 括号：每一对括号一个唯一颜色（开口/闭口同色）
_bracket_colors = _distinct_colors(600, 0.95, 0.55)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _write(z, name, data):
    """确定性写入 zip 条目（固定时间戳，保证重复生成结果一致）。"""
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    z.writestr(info, data)


def rpr(color=None, highlight=None, italic=False, underline=False, bold=False):
    p = []
    if bold:
        p.append("<w:b/><w:bCs/>")
    if italic:
        p.append("<w:i/><w:iCs/>")
    if underline:
        p.append('<w:u w:val="single"/>')
    if color is not None:
        p.append(f'<w:color w:val="{color}"/>')
    if highlight:
        p.append(f'<w:highlight w:val="{highlight}"/>')
    return "".join(p)


def run(text, **kw):
    pr = rpr(**kw)
    return f'<w:r><w:rPr>{pr}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


def para(runs):
    return "<w:p>" + "".join(runs) + "</w:p>"


# ---------- DSL --------------------------------------------------------------
def I(name):
    return ("id", name)


def TOK(kind):
    return ("tok", kind)


def RICH(text, **fmt):
    return ("rich", text, fmt)


def G(*items):
    return ("grp", list(items))


def LAM(params, *body):
    return G(TOK("lambda"), G(*[I(p) for p in params]), *body)


LET = TOK("let")
PR = TOK("print")


def render(term, out):
    kind = term[0]
    if kind == "id":
        name = term[1]
        out.append(run(MEOW, color=id_color(name)))
    elif kind == "tok":
        out.append(run(MEOW, **STYLE[term[1]]))
    elif kind == "rich":
        c = _next_bracket_color()          # 每段富文本独立颜色；属性是下划线，不会和括号串扰
        out.append(run(MEOW, color=c, underline=True))
        out.append(run(term[1], **term[2]))
        out.append(run(MEOW, color=c, underline=True))
    elif kind == "grp":
        c = _next_bracket_color()
        out.append(run(MEOW, color=c, italic=True))
        for t in term[1]:
            render(t, out)
        out.append(run(MEOW, color=c, italic=True))
    else:
        raise ValueError(kind)


_bc_cursor = [0]


def _next_bracket_color():
    c = _bracket_colors[_bc_cursor[0] % len(_bracket_colors)]
    _bc_cursor[0] += 1
    return c


# ---------- 程序定义（纯 Meow 源码的抽象） ----------------------------------
def defs():
    D = []

    def add(name, value):
        D.append([LET, I(name), value])

    # 布尔 / 惰性 if
    add("TRUE",  LAM(["x", "y"], I("x")))
    add("FALSE", LAM(["x", "y"], I("y")))
    add("AND",   LAM(["a", "b"], G(I("a"), I("b"), I("FALSE"))))
    add("NOT",   LAM(["a"], G(I("a"), I("FALSE"), I("TRUE"))))
    add("FORCE", LAM(["u"], I("u")))
    add("IF",    LAM(["c", "t", "f"], G(G(I("c"), I("t"), I("f")), I("FORCE"))))

    # 邱奇数
    add("ZERO", LAM(["f", "x"], I("x")))
    add("SUCC", LAM(["n"], LAM(["f", "x"], G(I("f"), G(I("n"), I("f"), I("x"))))))
    add("ADD",  LAM(["m", "n"], LAM(["f", "x"],
                                    G(I("m"), I("f"), G(I("n"), I("f"), I("x"))))))
    add("MUL",  LAM(["m", "n"], LAM(["f", "x"],
                                    G(I("m"), LAM(["y"], G(I("n"), I("f"), I("y"))), I("x")))))
    add("PRED", LAM(["n"], LAM(["f", "x"],
                                G(G(I("n"),
                                    LAM(["g"], LAM(["h"], G(I("h"), G(I("g"), I("f"))))),
                                    LAM(["u"], I("x"))),
                                  LAM(["u"], I("u"))))))
    add("SUB",  LAM(["m", "n"], LAM(["f", "x"],
                                    G(G(I("n"), I("PRED"), I("m")), I("f"), I("x")))))
    add("ISZERO", LAM(["n"], G(I("n"), LAM(["x"], I("FALSE")), I("TRUE"))))
    add("LEQ", LAM(["m", "n"], G(I("ISZERO"), G(I("SUB"), I("m"), I("n")))))
    add("EQ",  LAM(["m", "n"], G(I("AND"), G(I("LEQ"), I("m"), I("n")),
                                          G(I("LEQ"), I("n"), I("m")))))
    add("LT",  LAM(["m", "n"], G(I("AND"), G(I("LEQ"), I("m"), I("n")),
                                          G(I("NOT"), G(I("EQ"), I("m"), I("n"))))))
    add("MOD", LAM(["m", "n"], G(I("IF"),
                                 G(I("LT"), I("m"), I("n")),
                                 LAM(["u"], I("m")),
                                 LAM(["u"], G(I("MOD"), G(I("SUB"), I("m"), I("n")), I("n"))))))
    add("DIVIDES", LAM(["d", "n"], G(I("ISZERO"), G(I("MOD"), I("n"), I("d")))))
    # 注意：内层 IF 必须包在 thunk 里，否则会作为外层 IF 的参数被“提前求值”
    add("HASDIV", LAM(["d", "n"], G(I("IF"),
                                    G(I("EQ"), I("d"), I("n")),
                                    LAM(["u"], I("FALSE")),
                                    LAM(["u"], G(I("IF"),
                                                G(I("DIVIDES"), I("d"), I("n")),
                                                LAM(["u"], I("TRUE")),
                                                LAM(["u"], G(I("HASDIV"), G(I("SUCC"), I("d")), I("n"))))))))
    add("PRIME", LAM(["n"], G(I("NOT"),
                              G(I("HASDIV"), G(I("SUCC"), G(I("SUCC"), I("ZERO"))), I("n")))))
    add("SHOW", LAM(["n", "label"], G(I("IF"),
                                      G(I("PRIME"), I("n")),
                                      LAM(["u"], G(PR, G(I("label"), RICH(" is prime")))),
                                      LAM(["u"], G(PR, G(I("label"), RICH(" is NOT prime")))))))

    # 数字
    add("ONE", G(I("SUCC"), I("ZERO")))
    for i, name in enumerate(["TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN",
                              "EIGHT", "NINE", "TEN", "ELEVEN", "TWELVE", "THIRTEEN"], start=2):
        prev = ["ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN",
                "EIGHT", "NINE", "TEN", "ELEVEN", "TWELVE"][i - 2]
        add(name, G(I("SUCC"), I(prev)))
    add("SEVENTEEN",   G(I("ADD"), G(I("MUL"), I("FOUR"), I("FOUR")), I("ONE")))
    add("TWENTY_FIVE", G(I("MUL"), I("FIVE"), I("FIVE")))
    add("NINETY_ONE",  G(I("MUL"), I("SEVEN"), I("THIRTEEN")))
    add("NINETY_SEVEN",
        G(I("ADD"), G(I("MUL"), I("FOUR"), G(I("ADD"), I("FOUR"), G(I("MUL"), I("FOUR"), I("FIVE")))), I("ONE")))
    return D


def tests():
    cases = [("TWO", "2"), ("THREE", "3"), ("FOUR", "4"), ("FIVE", "5"),
             ("SEVEN", "7"), ("ELEVEN", "11"), ("THIRTEEN", "13"),
             ("SEVENTEEN", "17"), ("TWENTY_FIVE", "25"),
             ("NINETY_ONE", "91"), ("NINETY_SEVEN", "97")]
    out = []
    for name, label in cases:
        out.append(G(I("SHOW"), I(name), RICH(label)))
    return out


def main():
    paragraphs = []
    # 标题
    paragraphs.append(para([
        run(MEOW, **STYLE["print"]),
        run(MEOW, color="808080", underline=True),
        run("Meow prime calculator (Church encoding)"),
        run(MEOW, color="808080", underline=True),
    ]))
    for stmt in defs():
        runs = []
        for t in stmt:
            render(t, runs)
        paragraphs.append(para(runs))
    for stmt in tests():
        runs = []
        render(stmt, runs)
        paragraphs.append(para(runs))

    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>" + "".join(paragraphs) + "<w:sectPr/></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(root, "src")
    os.makedirs(src, exist_ok=True)
    out = os.path.join(src, "primes.docx")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        _write(z, "[Content_Types].xml", content_types)
        _write(z, "_rels/.rels", rels)
        _write(z, "word/document.xml", document)
    print("wrote", out, "  identifiers:", len(_id_colors), " bracket pairs:", _bc_cursor[0])


if __name__ == "__main__":
    main()
