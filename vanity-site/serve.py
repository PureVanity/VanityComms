#!/usr/bin/env python3
"""
Tiny local server for testing the Spotify login locally.

Run this from inside the vanity-site folder:
    python3 serve.py

Then open:
    http://127.0.0.1:25566/

Click "Connect Spotify" as normal. When Spotify redirects back to
http://127.0.0.1:25566/callback?code=... this server will serve
index.html for that path too (since /callback isn't a real file),
and the page's own JS picks the ?code= out of the URL and finishes
the login.
"""
import datetime
import http.server
import json
import os
import socketserver
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

PORT = 25566
HOST = "127.0.0.1"
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def fetch_latest_upload():
    def fetch_feed(url):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()

    def get_channel_id():
        page_url = "https://www.youtube.com/@FaIseVanity"
        req = urllib.request.Request(page_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")

        marker = "https://www.youtube.com/feeds/videos.xml?channel_id="
        idx = html.find(marker)
        if idx != -1:
            start = idx + len(marker)
            end = start
            while end < len(html) and html[end].isalnum():
                end += 1
            return html[start:end]

        # Try embedded channel ID references as fallback.
        for token in ['\\"channelId\\":\\"', '"channelId":"']:
            idx = html.find(token)
            if idx != -1:
                start = idx + len(token)
                end = start
                while end < len(html) and html[end].isalnum():
                    end += 1
                return html[start:end]
        return None

    feed_url = "https://www.youtube.com/feeds/videos.xml?user=FaIseVanity"
    try:
        payload = fetch_feed(feed_url)
    except (urllib.error.HTTPError, urllib.error.URLError):
        channel_id = get_channel_id()
        if channel_id:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            payload = fetch_feed(feed_url)
        else:
            raise

    root = ET.fromstring(payload)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
    }
    entry = root.find("atom:entry", ns)
    if entry is None:
        return {"videoUrl": "https://www.youtube.com/@FaIseVanity"}

    title = (entry.findtext("atom:title", default="Recent upload", namespaces=ns) or "Recent upload").strip()
    video_id = entry.findtext("yt:videoId", default="", namespaces=ns) or ""
    video_url = None
    for link in entry.findall("atom:link", ns):
        if link.get("rel") == "alternate":
            video_url = link.get("href")
            break

    if video_id:
        video_url = f"https://youtu.be/{video_id}"

    published = entry.findtext("atom:published", default="", namespaces=ns) or entry.findtext("atom:updated", default="", namespaces=ns) or ""
    published_dt = None
    if published:
        try:
            published_dt = datetime.datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            published_dt = None

    next_upload_dt = None
    if published_dt:
        interval_days = int(os.environ.get("UPLOAD_INTERVAL_DAYS", "7"))
        next_upload_dt = published_dt + datetime.timedelta(days=interval_days)

    return {
        "title": title,
        "videoUrl": video_url or "https://www.youtube.com/@FaIseVanity",
        "publishedAt": published,
        "nextUploadAt": next_upload_dt.isoformat() if next_upload_dt else None,
    }


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/latest-video"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            try:
                payload = json.dumps(fetch_latest_upload()).encode("utf-8")
            except (urllib.error.URLError, TimeoutError, ET.ParseError) as exc:
                payload = json.dumps({"videoUrl": "https://www.youtube.com/@FaIseVanity", "error": str(exc)}).encode("utf-8")
            self.wfile.write(payload)
            return

        # Strip query string, check if the path is a real file (e.g. /assets/foo.png).
        clean_path = self.path.split("?")[0]
        fs_path = self.translate_path(clean_path)
        if not os.path.isfile(fs_path):
            # Not a real file (e.g. /callback) -> serve index.html so the
            # page's JS can read ?code= from the URL and finish Spotify login.
            self.path = "/index.html"
        return super().do_GET()


if __name__ == "__main__":
    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        print(f"Serving vanity-site at http://{HOST}:{PORT}  (Ctrl+C to stop)")
        httpd.serve_forever()
