#!/usr/bin/env python3
"""公式サイトの URL を IndexNow（Bing ほか）へ通知する。

GitHub Pages に push して反映を待ってから実行する。
キーファイルが公開 URL で読めることを確認してから、sitemap.xml の全 URL を送る。

使い方:
  python3 tools/indexnow_submit.py            # 送信
  python3 tools/indexnow_submit.py --dry-run  # 送信せずに内容だけ表示
"""
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOST = "araiyusukeryudo507-coder.github.io"
BASE = f"https://{HOST}/arai-hp/"
ENDPOINT = "https://api.indexnow.org/indexnow"


def find_key():
    keys = [p for p in ROOT.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}\.txt", p.name)]
    if len(keys) != 1:
        sys.exit(f"キーファイルが見つからないか複数あります: {[p.name for p in keys]}")
    return keys[0].stem


def sitemap_urls():
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>(.*?)</loc>", xml)


def main():
    dry = "--dry-run" in sys.argv
    key = find_key()
    key_location = f"{BASE}{key}.txt"
    urls = sitemap_urls()
    payload = {"host": HOST, "key": key, "keyLocation": key_location, "urlList": urls}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if dry:
        return

    try:
        with urllib.request.urlopen(key_location, timeout=20) as r:
            body = r.read().decode().strip()
    except urllib.error.URLError as e:
        sys.exit(f"キーファイルが公開 URL で読めません（push 済みか確認）: {e}")
    if body != key:
        sys.exit("公開中のキーファイルの中身がキーと一致しません")

    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"送信しました: HTTP {r.status}")
    except urllib.error.HTTPError as e:
        sys.exit(f"送信失敗: HTTP {e.code} {e.read().decode(errors='replace')[:300]}")


if __name__ == "__main__":
    main()
