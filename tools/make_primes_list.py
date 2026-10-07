#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纯 Meow：从小到大打印质数，并把质数以【十进制数字】形式输出。

复用 make_primes.py 里的 DSL 与邱奇编码，再新增：
  DIV        整除（重复减法）
  HASDIV     试除到 sqrt(n)（用 MUL + LT 提前停止）
  PRIME      n 是否为质数
  PRINTDIGIT 把邱奇数 0..9 映射成一个字符（嵌套 IF 选择）
  PRINTNUM   递归打印十进制各位（最高位在前）
  WHENPRIME  若 n 为质数则打印 n + 换行
  LOOP       从 k 数到 limit，逐个判断
"""
import os
import zipfile
import make_primes as B

I, G, LAM, RICH, LET, PR = B.I, B.G, B.LAM, B.RICH, B.LET, B.PR

DIGITS = ["ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"]


def extra_defs():
    E = []

    def add(name, val):
        E.append([LET, I(name), val])

    # 整除：m < n 时返回 0，否则 SUCC (DIV (m-n) n)
    add("DIV", LAM(["m", "n"], G(I("IF"),
                                 G(I("LT"), I("m"), I("n")),
                                 LAM(["u"], I("ZERO")),
                                 LAM(["u"], G(I("SUCC"),
                                             G(I("DIV"), G(I("SUB"), I("m"), I("n")), I("n")))))))

    # 试除到 sqrt(n)：n < d*d 就停（说明没有因子）
    add("HASDIV", LAM(["d", "n"], G(I("IF"),
                                    G(I("LT"), I("n"), G(I("MUL"), I("d"), I("d"))),
                                    LAM(["u"], I("FALSE")),
                                    LAM(["u"], G(I("IF"),
                                                G(I("DIVIDES"), I("d"), I("n")),
                                                LAM(["u"], I("TRUE")),
                                                LAM(["u"], G(I("HASDIV"),
                                                            G(I("SUCC"), I("d")), I("n"))))))))
    add("PRIME", LAM(["n"], G(I("NOT"),
                              G(I("HASDIV"), G(I("SUCC"), G(I("SUCC"), I("ZERO"))), I("n")))))

    # 一位数字 -> 一个字符【文本】：d==0 ? "0" : d==1 ? "1" : ... : d==9 ? "9" : ""
    # 注意：Meow 的 print 每次都会换行，所以这里必须返回文本、最后统一打印一次。
    def print_digit():
        def go(i):
            if i > 9:
                return LAM(["u"], RICH(""))           # 兜底：空文本
            return G(I("IF"),
                     G(I("EQ"), I("d"), I(DIGITS[i])),
                     LAM(["u"], RICH(str(i))),
                     LAM(["u"], go(i + 1)))            # 内层 IF 必须 thunk，否则被提前求值
        return LAM(["d"], go(0))

    add("PRINTDIGIT", print_digit())

    # 十进制文本：n < 10 ? 该位 : 拼接( PRINTNUM(n/10), PRINTDIGIT(n%10) )
    add("PRINTNUM", LAM(["n"], G(I("IF"),
                                 G(I("LT"), I("n"), I("TEN")),
                                 LAM(["u"], G(I("PRINTDIGIT"), I("n"))),
                                 LAM(["u"],
                                     G(G(I("PRINTNUM"), G(I("DIV"), I("n"), I("TEN"))),
                                       G(I("PRINTDIGIT"), G(I("MOD"), I("n"), I("TEN"))))))))

    add("WHENPRIME", LAM(["n"], G(I("IF"),
                                  G(I("PRIME"), I("n")),
                                  LAM(["u"], G(PR, G(I("PRINTNUM"), I("n")))),
                                  LAM(["u"], I("ZERO")))))

    # 从 k 到 limit（含）逐个判断并打印
    add("LOOP", LAM(["k", "limit"], G(I("IF"),
                                      G(I("LEQ"), I("k"), I("limit")),
                                      LAM(["u"], G(I("WHENPRIME"), I("k")),
                                               G(I("LOOP"), G(I("SUCC"), I("k")), I("limit"))),
                                      LAM(["u"], I("ZERO")))))

    add("HUNDRED", G(I("MUL"), I("TEN"), I("TEN")))
    return E


def main():
    paragraphs = []
    # 标题
    paragraphs.append(B.para([
        B.run(B.MEOW, **B.STYLE["print"]),
        B.run(B.MEOW, color="808080", underline=True),
        B.run("primes up to 100"),
        B.run(B.MEOW, color="808080", underline=True),
    ]))

    for stmt in B.defs() + extra_defs():
        runs = []
        for t in stmt:
            B.render(t, runs)
        paragraphs.append(B.para(runs))

    # 主表达式：(LOOP TWO HUNDRED)
    runs = []
    B.render(G(I("LOOP"), I("TWO"), I("HUNDRED")), runs)
    paragraphs.append(B.para(runs))

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
    out = os.path.join(src, "primes_list.docx")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        B._write(z, "[Content_Types].xml", content_types)
        B._write(z, "_rels/.rels", rels)
        B._write(z, "word/document.xml", document)
    print("wrote", out, " identifiers:", len(B._id_colors), " bracket pairs:", B._bc_cursor[0])


if __name__ == "__main__":
    main()
