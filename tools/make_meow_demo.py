#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generates a Meow language source file (a .docx document) from scratch.

Meow concepts used here:
  * every paragraph is one top-level expression
  * a "token" is a run whose text is one of the meow words (Meow/喵/にゃん/...)
  * the token's formatting (color/highlight/italic/underline/font/size) is its identity
  * italic meow  = brackets  ( ... )
  * underlined meow = string/rich-text literal  " ... "
  * builtins:  let (00B0F0 lightGray), lambda (00B050 lightGray),
               integer (000000 lightGray), print (EE0000 yellow)
  * anything else = user identifier
"""
import zipfile
import os

MEOW = "Meow"


def _write(z, name, data):
    """确定性写入 zip 条目（固定时间戳，保证重复生成结果一致）。"""
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    z.writestr(info, data)

# ---- builtin token styles (must match org.glavo.meow exactly) --------------
LET     = dict(color="00B0F0", highlight="lightGray")
LAMBDA  = dict(color="00B050", highlight="lightGray")
INTEGER = dict(color="000000", highlight="lightGray")
PRINT   = dict(color="EE0000", highlight="yellow")

# ---- user token styles -----------------------------------------------------
# Every user identifier must have its OWN formatting, otherwise Meow treats the
# tokens as the same identifier.
GREETING = dict(color="7030A0")
NAME     = dict(color="C00000")
JOIN     = dict(color="548235")
PARAM_A  = dict(color="ED7D31")
PARAM_B  = dict(color="2E75B6")
BIG_X    = dict(color="BF8F00", size="84")
BA = dict(italic=True, color="0070C0")       # bracket style A
BB = dict(italic=True, color="92D050")       # bracket style B
BC = dict(italic=True, color="FF00FF")       # bracket style C
RICH = dict(underline=True, color="C00000")  # rich-text / string delimiters


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rpr(color=None, highlight=None, italic=False, underline=False,
        bold=False, size=None, font=None):
    parts = []
    if font:
        parts.append(f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>')
    if bold:
        parts.append("<w:b/><w:bCs/>")
    if italic:
        parts.append("<w:i/><w:iCs/>")
    if underline:
        parts.append('<w:u w:val="single"/>')
    if color is not None:
        parts.append(f'<w:color w:val="{color}"/>')
    if size is not None:
        parts.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if highlight:
        parts.append(f'<w:highlight w:val="{highlight}"/>')
    return "".join(parts)


def run(text, **kw):
    p = rpr(**kw)
    r = f"<w:rPr>{p}</w:rPr>" if p else ""
    return f'<w:r>{r}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


def meow(style, text=MEOW):
    return run(text, **style)


def para(runs):
    return "<w:p>" + "".join(runs) + "</w:p>"


paragraphs = []

# 1) print "Hello, Meow!"  (rich text: bold + red run preserved by print)
paragraphs.append(para([
    meow(PRINT),
    meow(RICH),
    run("Hello, "),
    run("Meow!", bold=True, color="EE0000"),
    meow(RICH),
]))

# 2) let greeting = "Hello, "
paragraphs.append(para([
    meow(LET),
    run(MEOW, **GREETING),       # identifier: greeting
    meow(RICH),
    run("Hello, "),
    meow(RICH),
]))

# 3) let name = "World"
paragraphs.append(para([
    meow(LET),
    run(MEOW, **NAME),           # identifier: name
    meow(RICH),
    run("World"),
    meow(RICH),
]))

# 4) print (greeting name "!")   -> MeowText concatenation
paragraphs.append(para([
    meow(PRINT),
    meow(BA),
    run(MEOW, **GREETING),       # greeting
    run(MEOW, **NAME),           # name
    meow(RICH),
    run("!"),
    meow(RICH),
    meow(BA),
]))

# 5) let join = (lambda (a b) (a " & " b))
paragraphs.append(para([
    meow(LET),
    run(MEOW, **JOIN),           # identifier: join
    meow(BA),
    meow(LAMBDA),
    meow(BB),
    run(MEOW, **PARAM_A),        # parameter a
    run(MEOW, **PARAM_B),        # parameter b
    meow(BB),
    meow(BC),
    run(MEOW, **PARAM_A),        # a
    meow(RICH),
    run(" & "),
    meow(RICH),
    run(MEOW, **PARAM_B),        # b
    meow(BC),
    meow(BA),
]))

# 6) print (join "Cats" "Dogs")
paragraphs.append(para([
    meow(PRINT),
    meow(BA),
    run(MEOW, **JOIN),           # join
    meow(RICH),
    run("Cats"),
    meow(RICH),
    meow(RICH),
    run("Dogs"),
    meow(RICH),
    meow(BA),
]))

# 7) print (integer X)   where X has font size 42pt (w:sz is half-points)
paragraphs.append(para([
    meow(PRINT),
    meow(BA),
    meow(INTEGER),
    run(MEOW, **BIG_X),                     # identifier X, 42pt
    meow(BA),
]))

document = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    "<w:body>"
    + "".join(paragraphs)
    + "<w:sectPr/>"
    "</w:body></w:document>"
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
    'Target="word/document.xml"/>'
    "</Relationships>"
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
os.makedirs(SRC, exist_ok=True)
out = os.path.join(SRC, "hello_meow.docx")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    _write(z, "[Content_Types].xml", content_types)
    _write(z, "_rels/.rels", rels)
    _write(z, "word/document.xml", document)

print("wrote", out)
