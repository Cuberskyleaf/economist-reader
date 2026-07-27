#!/usr/bin/env python3
"""Extract articles from Economist EPUB files into JSON format."""

import json
import re
import zipfile
import sys
import warnings

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

BASE_DIR = Path(__file__).parent

def load_config():
    with open(BASE_DIR / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def clean_html(raw_html):
    """Remove HTML tags and clean up whitespace."""
    soup = BeautifulSoup(raw_html, "lxml")
    # Remove script/style
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def extract_title_from_html(soup):
    """Extract a plausible article title from HTML soup."""
    for tag in ["h1", "h2", "h3", "h4", "title"]:
        el = soup.find(tag)
        if el and el.get_text(strip=True):
            title = el.get_text(strip=True)
            # Filter out overly generic titles
            if len(title) > 3 and "economist" not in title.lower()[:20]:
                return title
    return None

def extract_epub(epub_path, output_dir):
    """Extract articles from an EPUB file. EPUB is a ZIP with XHTML content."""
    issue_name = epub_path.stem
    issue_output_dir = Path(output_dir) / issue_name
    issue_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"  提取: {epub_path.name} ...", end=" ", flush=True)

    articles = []

    try:
        with zipfile.ZipFile(epub_path, "r") as zf:
            # Find all XHTML/HTML files (skip TOC, nav, etc.)
            html_files = [
                name for name in zf.namelist()
                if name.lower().endswith((".xhtml", ".html", ".htm"))
                and "toc" not in name.lower()
                and "nav" not in name.lower()
                and "cover" not in name.lower()
                and "copyright" not in name.lower()
            ]

            for html_file in html_files:
                content = zf.read(html_file)
                soup = BeautifulSoup(content, "lxml")

                # Extract body text
                body = soup.find("body")
                if not body:
                    continue

                raw_text = body.get_text(separator="\n", strip=True)
                if not raw_text or len(raw_text) < 100:
                    continue  # Skip very short sections

                title = extract_title_from_html(soup)
                if not title:
                    # Use the filename as fallback
                    title = Path(html_file).stem.replace("_", " ").replace("-", " ").strip()

                # Count words
                word_count = len(raw_text.split())

                article = {
                    "title": title,
                    "source_file": html_file,
                    "word_count": word_count,
                    "text": raw_text
                }
                articles.append(article)

    except zipfile.BadZipFile:
        print("✗ (不是有效的 EPUB/ZIP 文件)")
        return []

    # Sort by word count (longest first — likely main articles)
    articles.sort(key=lambda a: a["word_count"], reverse=True)

    # Remove very short articles (footnotes, indices, etc.)
    articles = [a for a in articles if a["word_count"] >= 50]

    # Save extracted articles as JSON
    output_file = issue_output_dir / "articles.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    # Also save individual text files
    texts_dir = issue_output_dir / "texts"
    texts_dir.mkdir(exist_ok=True)
    for i, article in enumerate(articles):
        safe_title = re.sub(r'[\\/*?:"<>|]', "", article["title"])[:80].strip()
        txt_path = texts_dir / f"{i+1:02d}_{safe_title}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"标题: {article['title']}\n")
            f.write(f"词数: {article['word_count']}\n")
            f.write("=" * 50 + "\n\n")
            f.write(article["text"])

    print(f"✓ ({len(articles)} 篇文章)")
    return articles

def main():
    config = load_config()
    issues_dir = BASE_DIR / config["issues_dir"]
    extracted_dir = BASE_DIR / config["extracted_dir"]
    extracted_dir.mkdir(parents=True, exist_ok=True)

    epub_files = sorted(issues_dir.glob("*.epub"))

    if not epub_files:
        print("没有找到 EPUB 文件。请先运行 downloader.py 下载期刊。")
        return

    print(f"=== 经济学人文章提取器 ===")
    print(f"找到 {len(epub_files)} 个 EPUB 文件\n")

    total_articles = 0
    for epub_path in epub_files:
        # Skip if already extracted
        issue_output_dir = extracted_dir / epub_path.stem
        if (issue_output_dir / "articles.json").exists():
            print(f"  ⊘ {epub_path.stem} (已提取)")
            continue

        articles = extract_epub(epub_path, extracted_dir)
        total_articles += len(articles)

    print(f"\n完成: 共提取 {total_articles} 篇文章")

if __name__ == "__main__":
    main()
