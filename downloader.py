#!/usr/bin/env python3
"""Download latest Economist issues from GitHub using git sparse-checkout (no API limit)."""

import json
import os
import re
import subprocess
import sys
import shutil
from pathlib import Path
from datetime import date, timedelta

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent
GIT_URL = "https://github.com/hehonghui/awesome-english-ebooks.git"
REPO_PATH = "01_economist"

# Unicode-safe symbols
CHECK = "[OK]"
CROSS = "[SKIP]"
STAR = "[*]"

def load_config():
    with open(BASE_DIR / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def run_git(args, cwd=None):
    """Run a git command with UTF-8 encoding."""
    return subprocess.run(
        ["git"] + args,
        cwd=cwd or str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120
    )

def main():
    config = load_config()
    issues_dir = BASE_DIR / config["issues_dir"]
    issues_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = BASE_DIR / "data" / ".repo_tmp"

    print("=== 经济学人下载器 ===")
    print(f"源: {GIT_URL}")
    print()

    # Check git availability
    if run_git(["--version"]).returncode != 0:
        print("错误: 未找到 Git。请安装 Git 后重试。")
        print("下载地址: https://git-scm.com/download/win")
        sys.exit(1)

    # Clone or update the repo with sparse checkout
    if (temp_dir / ".git").exists():
        print("更新仓库索引...")
        run_git(["fetch", "--depth", "1", "origin", "master"], cwd=temp_dir)
    else:
        print("首次克隆仓库 (仅索引，不下载文件)...")
        temp_dir.mkdir(parents=True, exist_ok=True)
        result = run_git([
            "clone", "--depth", "1", "--filter=blob:none",
            "--sparse", GIT_URL, str(temp_dir)
        ])
        if result.returncode != 0:
            print(f"克隆失败: {result.stderr}")
            sys.exit(1)

    # List remote directories without downloading files
    result = run_git(["ls-tree", "-d", "--name-only", f"origin/master:{REPO_PATH}"], cwd=temp_dir)
    if result.returncode != 0:
        print(f"列出目录失败: {result.stderr}")
        sys.exit(1)

    all_issues = sorted([d for d in result.stdout.strip().split("\n") if d.startswith("te_")])
    print(f"远程共 {len(all_issues)} 期期刊")
    print(f"最新一期: {all_issues[-1] if all_issues else 'N/A'}")
    print()

    # Determine which issues to download
    download_all = "--all" in sys.argv
    num_latest = 4

    if download_all:
        to_download = all_issues
        print(f"模式: 下载全部 ({len(to_download)} 期)")
    else:
        to_download = all_issues[-num_latest:]
        print(f"模式: 下载最新 {num_latest} 期")

    print()

    downloaded = 0
    skipped = 0

    for issue_name in to_download:
        local_epub = issues_dir / f"{issue_name}.epub"
        if local_epub.exists():
            print(f"  {CROSS} {issue_name} (已存在)")
            skipped += 1
            continue

        sparse_path = f"{REPO_PATH}/{issue_name}"
        result = run_git(["sparse-checkout", "add", "", sparse_path], cwd=temp_dir)
        if result.returncode != 0:
            print(f"  {CROSS} {issue_name}: sparse-checkout 失败")
            continue

        result = run_git(["checkout"], cwd=temp_dir)
        if result.returncode != 0:
            print(f"  {CROSS} {issue_name}: checkout 失败")
            continue

        issue_temp_dir = temp_dir / sparse_path
        epub_files = list(issue_temp_dir.glob("*.epub"))
        if epub_files:
            epub_file = epub_files[0]
            shutil.copy2(epub_file, local_epub)
            size_mb = local_epub.stat().st_size / (1024 * 1024)
            print(f"  {CHECK} {issue_name} ({size_mb:.1f} MB)")
            downloaded += 1
        else:
            print(f"  {CROSS} {issue_name}: 未找到 EPUB 文件")

    print()
    print(f"完成: 下载 {downloaded} 期, 跳过 {skipped} 期")

    local_files = sorted(issues_dir.glob("*.epub"))
    print(f"\n本地共 {len(local_files)} 期:")
    for f in local_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  📚 {f.stem} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
