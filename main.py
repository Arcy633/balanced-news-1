from flask import Flask, render_template
import feedparser
import sqlite3
import time
import threading
from datetime import datetime

app = Flask(__name__)

DB_FILE = "news.db"
RSS_FEEDS = [
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.bbci.co.uk/news/rss.xml"
]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT UNIQUE,
                    link TEXT,
                    published TEXT,
                    thumbnail TEXT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()

def fetch_news():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            published = entry.get("published", datetime.utcnow().isoformat())
            thumbnail = ""
            if "media_content" in entry and entry.media_content:
                thumbnail = entry.media_content[0].get("url", "")
            elif "links" in entry:
                for l in entry.links:
                    if l.get("type", "").startswith("image"):
                        thumbnail = l["href"]
                        break
            try:
                c.execute("INSERT INTO news (title, link, published, thumbnail) VALUES (?, ?, ?, ?)", 
                          (title, link, published, thumbnail))
            except sqlite3.IntegrityError:
                continue
    conn.commit()
    conn.close()

def refresh_news_periodically():
    while True:
        fetch_news()
        time.sleep(1800)  # 30 minutes

@app.route("/")
def index():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT title, link, published, thumbnail FROM news ORDER BY date_added DESC")
    rows = c.fetchall()
    conn.close()
    return render_template("index.html", articles=rows)

if __name__ == "__main__":
    init_db()
    fetch_news()
    threading.Thread(target=refresh_news_periodically, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
