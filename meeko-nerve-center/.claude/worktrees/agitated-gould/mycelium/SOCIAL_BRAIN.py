#!/usr/bin/env python3
"""
SOCIAL_BRAIN.py — AI generates + posts to all social platforms autonomously.

Pipeline:
  1. Read cycle_brief + content_harvest + published_articles
  2. AI generates platform-optimized posts for each platform
  3. Posts to: Twitter/X (v2 API), Bluesky (AT Protocol), Mastodon (API)
  4. Stores all posts in social_brain_log.json

100% autonomous social presence.
Reads:  data/cycle_brief.json, data/content_harvest.json, data/published_articles.json
Writes: data/social_brain_log.json
"""
import json, os, re
import urllib.request, urllib.error
import base64
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")
DATA.mkdir(exist_ok=True)

# Credentials
X_KEY    = (os.environ.get("X_API_KEY") or "").strip()
X_SECRET = (os.environ.get("X_API_SECRET") or "").strip()
X_TOKEN  = (os.environ.get("X_ACCESS_TOKEN") or "").strip()
X_TSECRET= (os.environ.get("X_ACCESS_SECRET") or "").strip()
BS_HANDLE= (os.environ.get("BLUESKY_HANDLE") or "").strip()
BS_PASS  = (os.environ.get("BLUESKY_APP_PASSWORD") or "").strip()
MASTO_TOKEN  = (os.environ.get("MASTODON_ACCESS_TOKEN") or "").strip()
MASTO_BASE   = (os.environ.get("MASTODON_API_BASE_URL") or "").strip()

def load_json(p, default=None):
    try:
        f = Path(p)
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception: pass
    return default or {}

def _http(url, headers, body=None, method="POST"):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def ai_generate_posts(context, article_url=""):
    """Generate platform-optimized posts from context."""
    try:
        from AI_CLIENT import ask_json
        system = "You are a social media AI for Gaza Rose Gallery. Authentic, mission-driven, never spammy. 70% revenue to PCRF."
        link = f"\n\nLink: {article_url}" if article_url else ""
        prompt = f"""Generate social media posts for these platforms based on this context:

Context:
- Phase: {context.get('phase','PRE_REVENUE')}
- Focus: {context.get('focus','')}
- Revenue: ${context.get('revenue',0):.2f} raised for PCRF
- Latest insight: {str(context.get('insight',''))[:200]}
- Article: {str(context.get('article_title',''))[:100]}{link}

Return JSON:
{{
  "twitter": "tweet max 270 chars. Authentic, include relevant hashtags. End with PCRF mention if natural.",
  "bluesky": "post max 290 chars. Same vibe, slightly warmer tone.",
  "mastodon": "post up to 450 chars. More detailed, add context, hashtags at end.",
  "thread_hook": "first tweet of a potential thread (max 270 chars) — a bold statement or question"
}}
"""
        result = ask_json([{"role": "user", "content": prompt}], system=system)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        msg = f"SolarPunk AI is running: {context.get('focus','building toward $1 first sale')} 🌱 #AI #OpenSource #Gaza"
        return {"twitter": msg[:270], "bluesky": msg[:290], "mastodon": msg[:450], "thread_hook": msg[:270]}

def post_mastodon(text):
    if not MASTO_TOKEN:
        return {"skipped": "no MASTODON_ACCESS_TOKEN"}
    base = MASTO_BASE.rstrip("/")
    result = _http(f"{base}/api/v1/statuses",
        {"Authorization": f"Bearer {MASTO_TOKEN}", "Content-Type": "application/json"},
        {"status": text[:500]})
    return {"id": result.get("id",""), "url": result.get("url",""), "error": result.get("error")}

def post_bluesky(text):
    if not BS_HANDLE or not BS_PASS:
        return {"skipped": "no BLUESKY_HANDLE or BLUESKY_APP_PASSWORD"}
    # Auth
    auth = _http("https://bsky.social/xrpc/com.atproto.server.createSession",
        {"Content-Type": "application/json"},
        {"identifier": BS_HANDLE, "password": BS_PASS})
    if not auth.get("accessJwt"):
        return {"error": f"bluesky auth failed: {auth.get('error','')}"}
    # Post
    result = _http("https://bsky.social/xrpc/com.atproto.repo.createRecord",
        {"Authorization": f"Bearer {auth['accessJwt']}", "Content-Type": "application/json"},
        {"repo": auth.get("did",""), "collection": "app.bsky.feed.post",
         "record": {"text": text[:300], "createdAt": datetime.now(timezone.utc).isoformat()}})
    uri = result.get("uri","")
    return {"uri": uri, "error": result.get("error")}

def post_twitter_oauth(text):
    """Post to Twitter v2 using OAuth 1.0a (stdlib only)."""
    if not all([X_KEY, X_SECRET, X_TOKEN, X_TSECRET]):
        return {"skipped": "missing Twitter OAuth credentials"}
    import hmac, hashlib, time, uuid, urllib.parse
    url = "https://api.twitter.com/2/tweets"
    oauth_params = {
        "oauth_consumer_key":     X_KEY,
        "oauth_nonce":            uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp":        str(int(time.time())),
        "oauth_token":            X_TOKEN,
        "oauth_version":          "1.0",
    }
    base_str = "&".join([
        "POST",
        urllib.parse.quote(url, safe=""),
        urllib.parse.quote("&".join(f"{urllib.parse.quote(k)}={urllib.parse.quote(v)}" for k,v in sorted(oauth_params.items())), safe="")
    ])
    signing_key = f"{urllib.parse.quote(X_SECRET)}&{urllib.parse.quote(X_TSECRET)}"
    sig = base64.b64encode(hmac.new(signing_key.encode(), base_str.encode(), hashlib.sha1).digest()).decode()
    oauth_params["oauth_signature"] = sig
    auth_header = "OAuth " + ", ".join(f'{k}="{urllib.parse.quote(v)}"' for k,v in sorted(oauth_params.items()))
    result = _http(url, {"Authorization": auth_header, "Content-Type": "application/json"}, {"text": text[:280]})
    tweet_id = result.get("data",{}).get("id","")
    return {"id": tweet_id, "error": result.get("detail") or result.get("error")}

def main():
    print("📣 SOCIAL_BRAIN — AI generating + posting to all platforms...")

    brief    = load_json("data/cycle_brief.json")
    harvest  = load_json("data/content_harvest.json")
    articles = load_json("data/published_articles.json", {"articles": []})
    prev_log = load_json("data/social_brain_log.json", {"posts": []})

    # Build context
    latest_article = articles.get("articles", [{}])[0] if articles.get("articles") else {}
    latest_url     = latest_article.get("devto",{}).get("url","") or ""
    latest_title   = latest_article.get("topic","")

    context = {
        "phase":         brief.get("phase","PRE_REVENUE"),
        "focus":         brief.get("focus_this_cycle",""),
        "revenue":       brief.get("revenue_usd", 0),
        "health":        brief.get("health_score", 0),
        "insight":       harvest.get("top_signal",""),
        "article_title": latest_title,
    }

    posts_generated = ai_generate_posts(context, latest_url)
    if not posts_generated:
        print("   ⚠ AI returned no posts")
        return

    cycle_posts = []

    # Mastodon
    masto_text = posts_generated.get("mastodon","")
    if masto_text:
        r = post_mastodon(masto_text)
        cycle_posts.append({"platform":"mastodon","text":masto_text,"result":r})
        print(f"   {'✓' if r.get('url') else '○'} Mastodon: {r.get('url') or r.get('skipped','err')}")

    # Bluesky
    bs_text = posts_generated.get("bluesky","")
    if bs_text:
        r = post_bluesky(bs_text)
        cycle_posts.append({"platform":"bluesky","text":bs_text,"result":r})
        print(f"   {'✓' if r.get('uri') else '○'} Bluesky: {r.get('uri') or r.get('skipped','err')}")

    # Twitter/X
    tw_text = posts_generated.get("twitter","")
    if tw_text:
        r = post_twitter_oauth(tw_text)
        cycle_posts.append({"platform":"twitter","text":tw_text,"result":r})
        print(f"   {'✓' if r.get('id') else '○'} Twitter: {r.get('id') or r.get('skipped','err')}")

    # Record timestamp
    for p in cycle_posts:
        p["posted_at"] = datetime.now(timezone.utc).isoformat()

    all_posts = cycle_posts + prev_log.get("posts",[])
    output = {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "cycle_posts":    len(cycle_posts),
        "total_posts":    len(all_posts),
        "posts":          all_posts[:200],
        "last_context":   context,
        "status":         "ok",
    }
    Path("data/social_brain_log.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"   {len(cycle_posts)} posts generated | {len([p for p in cycle_posts if not p['result'].get('skipped')])} attempted")

if __name__ == "__main__":
    main()
