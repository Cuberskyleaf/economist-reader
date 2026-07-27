# 📰 经济学人阅读器 &middot; The Economist Reader

每周自动下载最新一期《经济学人》，提取文章，在浏览器中阅读，点击任意单词即可查看音标、**中文翻译**和英文释义。

## ✨ 功能

- **自动下载** — 连接 GitHub 开源仓库，git 增量拉取最新期刊（每次仅下载新增）
- **文章提取** — EPUB 自动解析为结构化文章，按词数排序，长文优先
- **Web 阅读** — 简洁优雅的阅读界面，左侧目录导航
- **点击查词** — 点击任意单词弹窗显示：音标 + **中文翻译** + 英文释义
- **数据来源** — [hehonghui/awesome-english-ebooks](https://github.com/hehonghui/awesome-english-ebooks)（持续更新中）

## 🚀 快速开始

### 1. 安装依赖

`ash
pip install -r requirements.txt
`

### 2. 下载期刊

`ash
python downloader.py        # 下载最新 4 期
python downloader.py --all  # 下载全部历史期刊
`

### 3. 提取文章

`ash
python extractor.py
`

### 4. 开始阅读

`ash
python server.py
`

浏览器自动打开 http://127.0.0.1:8080。

### 🪟 Windows 用户

直接双击 un.bat，选择 [4] 下载 + 提取 + 开始阅读，一键搞定。

## 📅 每周更新

每周六新一期发布后：

`ash
python downloader.py
python extractor.py
`

刷新浏览器即可看到新文章，无需重启服务器。

## 🔍 查词效果

阅读时点击任意单词，弹窗显示：

`
economy
/ɪˈkɒn.ə.mi/  经济

noun
• The system of trade and industry by which wealth is created
• Careful management of available resources
...
`

## 📁 项目结构

`
economist-reader/
├── downloader.py         # git sparse-checkout 下载期刊
├── extractor.py          # EPUB 文章提取器
├── server.py             # Flask Web 阅读服务器
├── run.bat               # Windows 一键启动
├── config.json           # 配置文件
├── requirements.txt      # Python 依赖
└── templates/
    ├── index.html        # 期刊列表页
    └── reader.html       # 文章阅读页（含查词功能）
`

## 🛠 技术栈

- **Python 3** + Flask + BeautifulSoup + ebooklib
- **Git** 稀疏检出（避免 API 限流）
- **Free Dictionary API** — 英文释义
- **MyMemory API** — 英译中

## 📄 License

MIT
