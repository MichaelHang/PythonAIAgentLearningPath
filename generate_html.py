#!/usr/bin/env python
"""
HTML 页面生成脚本：把每个 .py 渲染成带侧边栏导航的代码清单页

用途：修改 .py 文件后运行本脚本，保证 HTML 页面与 .py 内容同步。
    python generate_html.py            # 重新生成全部页面
    python generate_html.py day01_practice_template.py   # 只生成指定页面

依赖：pip install pygments
"""

import sys
from pathlib import Path

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

根目录 = Path(__file__).parent

# 代码页清单：(py 文件, 页面标题)
页面清单 = [
    ("day01_practice_template.py", "🐍 Day01 Practice Template"),
    ("day01_practice_validator.py", "🐍 Day01 Practice Validator"),
    ("day02_practice_template.py", "🐍 Day02 Practice Template"),
    ("day02_practice_validator.py", "🐍 Day02 Practice Validator"),
    ("day03_practice_template.py", "🐍 Day03 Practice Template"),
    ("day03_practice_validator.py", "🐍 Day03 Practice Validator"),
    ("day04_practice_template.py", "🐍 Day04 Practice Template"),
    ("day04_practice_validator.py", "🐍 Day04 Practice Validator"),
    ("day05_practice_template.py", "🐍 Day05 Practice Template"),
    ("day05_practice_validator.py", "🐍 Day05 Practice Validator"),
    ("day06_practice_template.py", "🐍 Day06 Practice Template"),
    ("day06_practice_validator.py", "🐍 Day06 Practice Validator"),
    ("day07_practice_template.py", "🐍 Day07 Practice Template"),
    ("day07_practice_validator.py", "🐍 Day07 Practice Validator"),
    ("day08_practice_template.py", "🐍 Day08 Practice Template"),
    ("day08_practice_validator.py", "🐍 Day08 Practice Validator"),
    ("day09_practice_template.py", "🐍 Day09 Practice Template"),
    ("day09_practice_validator.py", "🐍 Day09 Practice Validator"),
    ("day10_practice_template.py", "🐍 Day10 Practice Template"),
    ("day10_practice_validator.py", "🐍 Day10 Practice Validator"),
    ("tutorial_01_decorators.py", "🐍 Tutorial 01 Decorators"),
    ("tutorial_02_async.py", "🐍 Tutorial 02 Async"),
    ("tutorial_03_real_api.py", "🐍 Tutorial 03 Real API"),
]

# 侧边栏导航：(href, 显示文字, 分组标题或 None)
导航 = [
    (None, None, None),  # 占位，见下方构造
]

导航项 = [
    ("index.html", "学习路线图 (主页)", None),
    ("ACCEPTANCE_CRITERIA.html", "验收标准", None),
    ("tutorial_01_decorators.html", "装饰器 8 步教程", "实战教程"),
    ("tutorial_02_async.html", "异步 9 步教程", None),
    ("tutorial_03_real_api.html", "真实 API 教程", None),
    ("day01_lesson.html", "Day 1 - 学习", "Day 1-3 (基础)"),
    ("day01_practice_template.html", "Day 1 - 模板", None),
    ("day01_practice_validator.html", "Day 1 - 验收", None),
    ("day02_lesson.html", "Day 2 - 学习", None),
    ("day02_practice_template.html", "Day 2 - 模板", None),
    ("day02_practice_validator.html", "Day 2 - 验收", None),
    ("day03_lesson.html", "Day 3 - 学习", None),
    ("day03_practice_template.html", "Day 3 - 模板", None),
    ("day03_practice_validator.html", "Day 3 - 验收", None),
    ("day04_lesson.html", "Day 4 - 学习", "Day 4-5 (LLM)"),
    ("day04_practice_template.html", "Day 4 - 模板", None),
    ("day04_practice_validator.html", "Day 4 - 验收", None),
    ("day05_lesson.html", "Day 5 - 学习", None),
    ("day05_practice_template.html", "Day 5 - 模板", None),
    ("day05_practice_validator.html", "Day 5 - 验收", None),
    ("day06_lesson.html", "Day 6 - 学习", "Day 6-7 (Agent)"),
    ("day06_practice_template.html", "Day 6 - 模板", None),
    ("day06_practice_validator.html", "Day 6 - 验收", None),
    ("day07_lesson.html", "Day 7 - 学习", None),
    ("day07_practice_template.html", "Day 7 - 模板", None),
    ("day07_practice_validator.html", "Day 7 - 验收", None),
    ("day08_lesson.html", "Day 8 - 学习", "Day 8-10 (高级)"),
    ("day08_practice_template.html", "Day 8 - 模板", None),
    ("day08_practice_validator.html", "Day 8 - 验收", None),
    ("day09_lesson.html", "Day 9 - 学习", None),
    ("day09_practice_template.html", "Day 9 - 模板", None),
    ("day09_practice_validator.html", "Day 9 - 验收", None),
    ("day10_lesson.html", "Day 10 - 学习", None),
    ("day10_practice_template.html", "Day 10 - 模板", None),
    ("day10_practice_validator.html", "Day 10 - 验收", None),
    ("day11_lesson.html", "Day 11 - 学习", "Day 11-15 (项目实战)"),
    ("day12_lesson.html", "Day 12 - 学习", None),
    ("day13_lesson.html", "Day 13 - 学习", None),
    ("day14_lesson.html", "Day 14 - 学习", None),
    ("day15_lesson.html", "Day 15 - 学习", None),
    ("project_day11_15/README.md", "项目脚手架", None),
]


def 提取样式() -> str:
    """从现有 day01 页面提取 <style> 内容（页面 CSS + Pygments 配色）"""
    源文件 = 根目录 / "day01_practice_template.html"
    if 源文件.exists():
        文本 = 源文件.read_text(encoding="utf-8")
        开始 = 文本.find("<style>")
        结束 = 文本.find("</style>")
        if 开始 != -1 and 结束 != -1 and ".nav-sidebar" in 文本:
            return 文本[开始 + len("<style>"):结束]
    raise SystemExit("❌ 找不到现有页面样式，请先从 git 恢复 day01_practice_template.html")


def 构造侧边栏(当前页面: str) -> str:
    parts = ['<div class="nav-sidebar">', "<h3>资源导航</h3>"]
    for href, 文字, 分组 in 导航项:
        if 分组:
            parts.append(f"<h4>{分组}</h4>")
        active = "active" if href == 当前页面 else ""
        parts.append(f'<a class="{active}" href="{href}">{文字}</a>')
    parts.append("</div>")
    return "\n".join(parts)


def 生成页面(py文件: str, 标题: str, 样式: str) -> str:
    py路径 = 根目录 / py文件
    html文件 = py文件.replace(".py", ".html")
    代码 = py路径.read_text(encoding="utf-8")
    formatter = HtmlFormatter(cssclass="highlight", nowrap=False)
    代码html = highlight(代码, PythonLexer(), formatter)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{标题}</title>
    <style>
{样式}
    </style>
</head>
<body>
<div class="nav-wrapper">
{构造侧边栏(html文件)}
<div class="main-content">
    <div class="header"><h1>{标题}</h1></div>
    <div class="content">
        <div class="file-info"><div class="info-left">📄 文件: <code>{py文件}</code></div><a class="download-btn" href="{py文件}" download>⬇ 下载 .py 文件</a></div>
{代码html}
    </div>
</div>
</div>
<button class="back-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" title="返回顶部">⬆</button>
<script>window.addEventListener("scroll",function(){{  var btn=document.querySelector(".back-top");  if(btn)btn.style.display=window.scrollY>300?"block":"none";}});</script>
</body>
</html>"""


def main():
    指定 = [a for a in sys.argv[1:] if a.endswith(".py")]
    样式 = 提取样式()
    生成数 = 0
    for py文件, 标题 in 页面清单:
        if 指定 and py文件 not in 指定:
            continue
        html文件 = 根目录 / py文件.replace(".py", ".html")
        if not (根目录 / py文件).exists():
            print(f"⚠️ 跳过（找不到 {py文件}）")
            continue
        html文件.write_text(生成页面(py文件, 标题, 样式), encoding="utf-8")
        print(f"✅ 已生成 {html文件.name}")
        生成数 += 1
    print(f"\n共生成 {生成数} 个页面")


if __name__ == "__main__":
    main()
