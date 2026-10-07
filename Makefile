# 便捷入口
PY ?= python3

.PHONY: all generate run build clean

all: generate

# 由 tools/ 下的脚本生成 src/ 下的 Meow 源程序（.docx）
generate:
	$(PY) tools/make_meow_demo.py
	$(PY) tools/make_primes.py
	$(PY) tools/make_primes_list.py

# 生成并运行示例
# 注：Meow 用 JLine 输出，重定向/管道时可能丢输出；真终端里直接运行即可。
run: generate
	java -jar meow.jar src/primes_list.docx

# 从上游构建解释器 meow.jar
build:
	./build.sh

clean:
	rm -f src/*.docx
