import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from openai import OpenAI

# 1. 厚生労働省のRSS（新着情報）を取得
url = "https://www.mhlw.go.jp/stf/news.rdf"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    xml_data = response.read()

root = ET.fromstring(xml_data)
# 最新のニュースを1つ取得
item = root.findall('.//{http://purl.org/rss/1.0/}item')[0]
news_title = item.find('{http://purl.org/rss/1.0/}title').text
news_link = item.find('{http://purl.org/rss/1.0/}link').text

# 2. OpenAI APIに接続して要約と3択を作成
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

prompt = f"""
以下の公的機関のニュースを若者向けに分かりやすく要約し、JSON形式のみで出力してください。
ニュースタイトル: {news_title}
リンク: {news_link}

【厳格な出力JSONフォーマット】
{{
  "id": 999,
  "tag": "🏛️ 行政・社会",
  "title": "若者向けのキャッチーなタイトル",
  "summary": "100文字程度の分かりやすい要約",
  "sourceUrl": "{news_link}",
  "sourceName": "厚生労働省 公式サイトで詳細を見る",
  "options": [
    {{ "text": "良いと思う！", "votes": 0 }},
    {{ "text": "悪いと思う！", "votes": 0 }},
    {{ "text": "分からない", "votes": 0 }}
  ]
}}
"""

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    response_format={ "type": "json_object" }
)

new_post = json.loads(completion.choices[0].message.content)

# 3. 既存のデータを読み込み、一番上に追加し、古いものを消す（最新50件のみ保持）
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# IDを重複しないように設定
new_post['id'] = data[0]['id'] + 1 if data else 1
data.insert(0, new_post)
data = data[:50] # ★ここを「3」から「50」に変更しました！

# 4. JSONを上書き保存
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
