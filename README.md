# meow-church

用 [Glavo/MeowLang](https://github.com/Glavo/MeowLang)（一个用 Word 文档写代码的「次世代」深奥语言）写的示例集合：
从 Hello World，到用**邱奇编码（Church encoding）** 在纯 Meow 里计算质数、并以十进制打印。

> `meow-church` = Meow + Church（阿隆佐·邱奇，λ 演算与邱奇编码的发明人）。

Meow 语言的核心设定：

- **源文件是 Microsoft Word 文档（`.docx`）**，每个段落是一条顶层表达式。
- **唯一的关键字是「猫叫」**：`Meow`、`喵`、`にゃん`、`nyan`、`мяу`……任意一种都行。
- **标识符的「名字」就是它的排版**：颜色、高亮（背景色）、粗体、斜体、下划线、字体、字号。
  只有排版完全相同的「猫叫」才会被当成同一个标识符。
- **斜体猫叫 = 括号 `( ... )`**，**下划线猫叫 = 字符串/富文本字面量 `" ... "`**。
- 内置词由固定的「颜色 + 高亮」组合识别：

| 内置词 | 颜色 | 高亮 | 含义 |
| --- | --- | --- | --- |
| `let` | `00B0F0` | lightGray | 绑定：`let 标识符 值` |
| `lambda` | `00B050` | lightGray | `lambda (参数…) 体` |
| `integer` | `000000` | lightGray | 把标识符的**字号**当作整数 |
| `print` | `EE0000` | yellow | 输出 |
| `readline` | `00B0F0` | yellow | 读取一行 |

## 这个程序做了什么

源文件：`src/hello_meow.docx`（由 `tools/make_meow_demo.py` 生成）。用 debug 模式可以看到它被解析成的 AST：

```text
[@print, "Hello, Meow!"]                              # print "Hello, Meow!"
[@let, $0, "Hello, "]                                 # let greeting = "Hello, "
[@let, $1, "World"]                                   # let name = "World"
[@print, [$0, $1, "!"]]                               # print (greeting name "!")  -> 文本拼接
[@let, $2, [@lambda, [$3, $4], [$3, " & ", $4]]]      # let join = (lambda (a b) (a " & " b))
[@print, [$2, "Cats", "Dogs"]]                        # print (join "Cats" "Dogs")
[@print, [@integer, $5]]                              # print (integer X)   X 字号 42pt
```

其中 `$0..$5` 是 6 个排版各不相同的用户标识符：

| 符号 | 颜色 | 含义 |
| --- | --- | --- |
| `$0` | `7030A0` | `greeting` |
| `$1` | `C00000` | `name` |
| `$2` | `548235` | `join` |
| `$3` | `ED7D31` | lambda 参数 `a` |
| `$4` | `2E75B6` | lambda 参数 `b` |
| `$5` | `BF8F00` (42pt) | `X`（`integer` 读取它的字号） |

## 运行

```bash
java -jar meow.jar src/hello_meow.docx
```

实际输出（`print` 会保留富文本的加粗/颜色）：

```text
Hello, Meow!        # 其中 "Meow!" 是加粗的红色
Hello, World!
Cats & Dogs
42
```

## 用纯 Meow 计算质数

`primes.docx` 是**纯 Meow** 程序（只用到 `let` / `lambda` / `print`，没有改解释器、没有新增内置），
它把邱奇编码（Church encoding）搬进了 Meow，从而在没有任何算术原语的语言里算出质数。

为什么可行：Meow 本质就是带绑定的 lambda 演算，是图灵完备的。用邱奇布尔 + 邱奇奇数可以表达
自然数、加法、乘法、前驱、减法与比较。程序里定义的核心组合子：

```text
TRUE  = (lambda (x y) x)                       FALSE = (lambda (x y) y)
AND   = (lambda (a b) (a b FALSE))             NOT   = (lambda (a) (a FALSE TRUE))
ZERO  = (lambda (f x) x)                       SUCC  = (lambda (n) (lambda (f x) (f (n f x))))
ADD   = (lambda (m n) (lambda (f x) (m f (n f x))))
MUL   = (lambda (m n) (lambda (f x) (m (lambda (y) (n f y)) x)))
PRED  = (lambda (n) (lambda (f x) ((n (lambda (g) (lambda (h) (h (g f)))) (lambda (u) x)) (lambda (u) u))))
SUB   = (lambda (m n) (lambda (f x) ((n PRED m) f x)))
ISZERO= (lambda (n) (n (lambda (x) FALSE) TRUE))
LEQ/EQ/LT = 由 ISZERO、SUB、AND、NOT 组合
MOD   = 递归：IF (m < n) m (MOD (m - n) n)
PRIME = (lambda (n) (NOT (HASDIV 2 n)))        HASDIV 从 2 试到 n
```

有两个「坑」，也正好体现了 Meow 的语义：

1. **严格求值**：函数参数会先被求值，所以没有短路求值。这里把分支包成 thunk
   （`(lambda (u) …)`），再用 `IF c t f = ((c t f) FORCE)` 手动强制，才实现惰性条件；
   嵌套的 `IF` 也必须包进 thunk，否则会作为参数被提前求值。
2. **参数个数必须精确**：`MeowLambda` 会校验实参个数，不能部分应用（没有柯里化），
   所以「返回一个函数」要用嵌套 lambda，比如 `SUCC n` 返回 `(lambda (f x) …)`。

运行：

```bash
java -jar meow.jar src/primes.docx
```

输出：

```text
Meow prime calculator (Church encoding)
2 is prime
3 is prime
4 is NOT prime
5 is prime
7 is prime
11 is prime
13 is prime
17 is prime
25 is NOT prime
91 is NOT prime
97 is prime
```

## 从小到大打印质数（十进制）

`primes_list.docx`（生成器 `make_primes_list.py`）更进一步：在纯 Meow 里把质数**以十进制数字**、
从小到大打印出来。为此又补齐了几个组合子：

```text
DIV        = (lambda (m n) 递归重复减法求整除)
HASDIV     = 试除到 sqrt(n)（用 MUL + LT 提前停止，比试到 n 快很多）
PRINTDIGIT = 把邱奇数 0..9 用嵌套 IF 映射成字符 "0".."9"
PRINTNUM   = 递归打印十进制各位（最高位在前）
WHENPRIME  = 若 n 为质数则打印 n
LOOP       = 从 k 数到 limit
```

这里又踩到一个 Meow 特性：**`print` 每次调用都会自动换行**，所以不能「一位一位地 print」，
必须先用 **MeowText 拼接**把整个十进制字符串拼出来，最后只 `print` 一次
（`PRINTNUM` 返回文本，而不是直接输出）。

运行：

```bash
java -jar meow.jar src/primes_list.docx
```

输出（约 15 秒）：

```text
primes up to 100
2
3
5
7
11
13
17
19
23
29
31
37
41
43
47
53
59
61
67
71
73
79
83
89
97
```

## 目录结构

```text
.
├── README.md              # 本说明
├── Makefile               # make generate / run / build / clean
├── build.sh               # 从上游克隆并构建 meow.jar
├── meow.jar               # 解释器（.gitignore 忽略，用 build.sh 生成）
├── src/                   # Meow 源程序（.docx）
│   ├── hello_meow.docx
│   ├── primes.docx
│   └── primes_list.docx
└── tools/                 # 生成 .docx 的脚本
    ├── make_meow_demo.py      # hello_meow.docx
    ├── make_primes.py          # primes.docx（含邱奇编码 DSL）
    └── make_primes_list.py     # primes_list.docx
```

常用命令：

```bash
make generate     # 重新生成 src/ 下所有 .docx
make run          # 生成并运行 primes_list
make build        # 构建 meow.jar（首次运行前需要）

java -jar meow.jar src/hello_meow.docx    # 直接运行任意程序
```

> 运行提示：Meow 用 JLine 输出，**在真终端里直接跑**即可；如果你要重定向到文件
> （`> log.txt`），JLine 会退化成带缓冲的 dumb terminal 而可能丢输出，此时可用
> `script -qec "java -jar meow.jar src/primes_list.docx" /dev/null` 包一层伪终端。

### 各文件说明

- `src/hello_meow.docx` —— 入门示例（富文本、`let`、`lambda`、`integer`）。
- `src/primes.docx` —— 纯 Meow 质数判定。
- `src/primes_list.docx` —— 纯 Meow、十进制、从小到大打印质数。
- `tools/make_*.py` —— 用 Python 手写 OOXML 生成上述 `.docx`（标识符/括号的排版即变量名）。
- `build.sh` —— 从 `Glavo/MeowLang` 克隆并构建 `meow.jar`。
