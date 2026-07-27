#!/usr/bin/env python3
"""Web reading server for The Economist - with word lookup dictionary."""

import json
import re
import sys
import webbrowser
from pathlib import Path
from flask import Flask, render_template, request, jsonify

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent

def load_config():
    with open(BASE_DIR / 'config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

app = Flask(__name__)


@app.route('/')
def index():
    config = load_config()
    extracted_dir = BASE_DIR / config['extracted_dir']
    issues = []
    if extracted_dir.exists():
        for d in sorted(extracted_dir.iterdir(), reverse=True):
            if d.is_dir():
                articles_file = d / 'articles.json'
                if articles_file.exists():
                    with open(articles_file, 'r', encoding='utf-8') as f:
                        articles = json.load(f)
                    display = d.name.replace('te_', '').replace('.', '年', 1).replace('.', '月', 1) + '日'
                    issues.append({
                        'id': d.name,
                        'display_date': display,
                        'article_count': len(articles)
                    })
    return render_template('index.html', issues=issues)


@app.route('/issue/<issue_id>')
def read_issue(issue_id):
    config = load_config()
    extracted_dir = BASE_DIR / config['extracted_dir']
    issue_dir = extracted_dir / issue_id
    articles_file = issue_dir / 'articles.json'

    if not articles_file.exists():
        return 'Journal not found.', 404

    with open(articles_file, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    for i, article in enumerate(articles):
        article['id'] = i
        paragraphs = []
        for line in article['text'].split('\n'):
            words = line.strip().split()
            if words:
                paragraphs.append(words)
        article['paragraphs'] = paragraphs

    article_idx = request.args.get('article', 0, type=int)
    current = articles[article_idx] if 0 <= article_idx < len(articles) else None

    display = issue_id.replace('te_', '').replace('.', '年', 1).replace('.', '月', 1) + '日'
    issue = {
        'id': issue_id,
        'display_date': display,
        'article_count': len(articles)
    }

    return render_template('reader.html',
                         issue=issue,
                         articles=articles,
                         current=current,
                         active_id=article_idx)


@app.route('/api/lookup')
def api_lookup():
    word = request.args.get('word', '').strip()
    if not word:
        return jsonify({'error': 'No word provided'})

    clean_word = re.sub(r'[^a-zA-Z-]', '', word).lower()
    if len(clean_word) < 2:
        return jsonify({'word': word, 'meanings': []})

    try:
        import urllib.request
        import urllib.error
        import concurrent.futures

        # Fetch English definition
        url_en = f'https://api.dictionaryapi.dev/api/v2/entries/en/{clean_word}'
        req_en = urllib.request.Request(url_en, headers={'User-Agent': 'EconomistReader/1.0'})
        with urllib.request.urlopen(req_en, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        # Fetch Chinese translation
        cn_translation = ''
        try:
            url_cn = f'https://api.mymemory.translated.net/get?q={clean_word}&langpair=en%7Czh-CN'
            req_cn = urllib.request.Request(url_cn, headers={'User-Agent': 'EconomistReader/1.0'})
            with urllib.request.urlopen(req_cn, timeout=4) as resp_cn:
                cn_data = json.loads(resp_cn.read().decode())
                cn_translation = cn_data.get('responseData', {}).get('translatedText', '')
        except Exception:
            pass

        if not data or not isinstance(data, list):
            return jsonify({'word': clean_word, 'meanings': []})

        entry = data[0]
        result = {
            'word': entry.get('word', clean_word),
            'phonetic': entry.get('phonetic', ''),
            'cn': cn_translation if cn_translation.lower() != clean_word.lower() else '',
            'meanings': []
        }

        if not result['phonetic'] and 'phonetics' in entry:
            for p in entry['phonetics']:
                if p.get('text'):
                    result['phonetic'] = p['text']
                    break

        for meaning in entry.get('meanings', []):
            pos = meaning.get('partOfSpeech', '')
            defs = []
            for d in meaning.get('definitions', [])[:4]:
                defs.append(d.get('definition', ''))
            if defs:
                result['meanings'].append({'pos': pos, 'defs': defs})

        return jsonify(result)

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return jsonify({'word': clean_word, 'meanings': []})
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download')
def download_page():
    return '''<!DOCTYPE html>
<html lang=\"zh-CN\">
<head><meta charset=\"UTF-8\"><title>Download</title>
<style>
body { font-family: \"Microsoft YaHei\", sans-serif; background: #f5f0eb; text-align: center; padding: 60px; }
h2 { color: #c41230; }
pre { background: #1a1a1a; color: #0f0; padding: 20px; border-radius: 10px; text-align: left; max-width: 600px; margin: 20px auto; overflow-x: auto; }
.btn { padding: 10px 24px; background: #c41230; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 1em; margin-top: 10px; text-decoration: none; display: inline-block; }
</style></head>
<body>
<h2>Download Issues</h2>
<p>Run in terminal:</p>
<pre>python downloader.py</pre>
<p>(Latest 4 issues, or --all for everything)</p>
<p>Then extract and start reading.</p>
<a href=\"/\" class=\"btn\">Back</a>
</body></html>'''


@app.route('/extract')
def extract_page():
    return '''<!DOCTYPE html>
<html lang=\"zh-CN\">
<head><meta charset=\"UTF-8\"><title>Extract</title>
<style>
body { font-family: \"Microsoft YaHei\", sans-serif; background: #f5f0eb; text-align: center; padding: 60px; }
h2 { color: #c41230; }
pre { background: #1a1a1a; color: #0f0; padding: 20px; border-radius: 10px; text-align: left; max-width: 600px; margin: 20px auto; overflow-x: auto; }
.btn { padding: 10px 24px; background: #c41230; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 1em; margin-top: 10px; text-decoration: none; display: inline-block; }
</style></head>
<body>
<h2>Extract Articles</h2>
<p>Run in terminal:</p>
<pre>python extractor.py</pre>
<p>Then return to homepage to read.</p>
<a href=\"/\" class=\"btn\">Back</a>
</body></html>'''


def main():
    config = load_config()
    host = config['server_host']
    port = config['server_port']

    print(f'=== The Economist Reader ===')
    print(f'Starting server: http://{host}:{port}')
    print(f'Press Ctrl+C to stop')

    webbrowser.open(f'http://{host}:{port}')
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()
