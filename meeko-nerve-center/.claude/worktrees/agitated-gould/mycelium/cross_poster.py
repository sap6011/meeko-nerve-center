#!/usr/bin/env python3
"""
cross_poster.py — Brain-Gated Multi-Platform Post Distributor
=============================================================
Third link in the missing connections chain (connections.json):
  monetization_tracker → signal_tracker → cross_poster → meeko_brain

Brain-gated: only posts if brain_state health >= threshold AND
             signal_tracker says content is ready AND
             platform hasn't been posted to this cycle.

Uses signal_tracker.py recommendations to decide WHERE and WHAT to post.
Executes the actual posting calls (Twitter OAuth, Reddit OAuth).
Logs every post attempt with result.

Reads:  data/signal_tracker.json     (what/where/when to post)
        data/social_latest.json      (ready tweets + reddit posts)
        data/brain_state.json        (health gate — skip if broken)
        data/cross_post_log.json     (dedup — don't double-post)
Writes: data/cross_post_log.json     (full audit trail)
"""
import os, json, requests, hashlib
from pathlib import Path
from datetime import datetime, timezone

X_API_KEY        = os.environ.get("X_API_KEY")
X_API_SECRET     = os.environ.get("X_API_SECRET")
X_ACCESS_TOKEN   = os.environ.get("X_ACCESS_TOKEN")
X_ACCESS_SECRET  = os.environ.get("X_ACCESS_SECRET")
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
REDDIT_SECRET    = os.environ.get("REDDIT_CLIENT_SECRET")
REDDIT_USER      = os.environ.get("REDDIT_USERNAME")
REDDIT_PASS      = os.environ.get("REDDIT_PASSWORD")

DATA          = Path("data")
MIN_HEALTH    = 30   # don't post if brain is in crisis
REDDIT_UA     = "SolarPunk/2.0 (Gaza Rose Gallery; cross_poster)"


def load_json(fname, default=None):
    fp = DATA / fname
    try:
        return json.loads(fp.read_text()) if fp.exists() else (default or {})
    except Exception:
        return default or {}


# ── Brain gate ──────────────────────────────────────────────────────────────

def brain_gate():
    """Return (allowed, reason). Block posting if system is in crisis."""
    brain = load_json("brain_state.json")
    score = brain.get("health_score", 0)
    if score < MIN_HEALTH:
        return False, f"health {score} < {MIN_HEALTH} — system not stable enough to post"
    return True, f"health {score} OK"


# ── Dedup ────────────────────────────────────────────────────────────────────

def content_hash(text):
    return hashlib.md5(text.encode()).hexdigest()[:12]


def already_posted(log, text, platform):
    posts = log.get("posts", [])
    h = content_hash(text)
    return any(p.get("hash") == h and p.get("platform") == platform for p in posts)


# ── Twitter posting ──────────────────────────────────────────────────────────

def post_twitter(tweet_text):
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
        return {"status": "skipped", "reason": "no_credentials"}
    try:
        import hmac, base64, time, urllib.parse
        url = "https://api.twitter.com/2/tweets"
        ts  = str(int(time.time()))
        nonce = hashlib.md5(ts.encode()).hexdigest()
        params = {
            "oauth_consumer_key": X_API_KEY, "oauth_nonce": nonce,
            "oauth_signature_method": "HMAC-SHA1", "oauth_timestamp": ts,
            "oauth_token": X_ACCESS_TOKEN, "oauth_version": "1.0",
        }
        base = "POST&" + urllib.parse.quote(url, safe="") + "&" + \
               urllib.parse.quote("&".join(f"{k}={urllib.parse.quote(str(v), safe='')}"
               for k, v in sorted(params.items())), safe="")
        key  = urllib.parse.quote(X_API_SECRET, safe="") + "&" + urllib.parse.quote(X_ACCESS_SECRET, safe="")
        sig  = base64.b64encode(
            hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()
        ).decode()
        params["oauth_signature"] = sig
        auth = "OAuth " + ", ".join(
            f'{k}="{urllib.parse.quote(str(v), safe="")}"' for k, v in sorted(params.items())
        )
        r = requests.post(url,
            headers={"Authorization": auth, "Content-Type": "application/json"},
            json={"text": tweet_text[:280]}, timeout=20)
        if r.status_code in (200, 201):
            return {"status": "posted", "id": r.json().get("data", {}).get("id")}
        return {"status": "failed", "code": r.status_code, "msg": r.text[:200]}
    except Exception as ex:
        return {"status": "error", "msg": str(ex)}


# ── Reddit posting ────────────────────────────────────────────────────────────

def post_reddit(subreddit, title, text):
    if not all([REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_USER, REDDIT_PASS]):
        return {"status": "skipped", "reason": "no_credentials"}
    try:
        tok = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_SECRET),
            data={"grant_type": "password", "username": REDDIT_USER, "password": REDDIT_PASS},
            headers={"User-Agent": REDDIT_UA}, timeout=15,
        )
        if tok.status_code != 200:
            return {"status": "failed", "reason": f"token {tok.status_code}"}
        token = tok.json().get("access_token", "")
        r = requests.post(
            "https://oauth.reddit.com/api/submit",
            headers={"Authorization": f"bearer {token}", "User-Agent": REDDIT_UA},
            data={"sr": subreddit, "kind": "self", "title": title, "text": text},
            timeout=20,
        )
        data = r.json()
        if r.status_code in (200, 201) and data.get("success"):
            return {"status": "posted"}
        return {"status": "failed", "code": r.status_code, "msg": str(data)[:200]}
    except Exception as ex:
        return {"status": "error", "msg": str(ex)}


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    DATA.mkdir(exist_ok=True)
    print("cross_poster — Brain-Gated Multi-Platform Distributor...")
    ts = datetime.now(timezone.utc).isoformat()

    # Brain gate
    allowed, reason = brain_gate()
    print(f"  Brain gate: {'PASS' if allowed else 'BLOCK'} ({reason})")

    log = load_json("cross_post_log.json", {"posts": [], "cycles": 0})
    log["cycles"] = log.get("cycles", 0) + 1

    if not allowed:
        log["last_skip"] = {"ts": ts, "reason": reason}
        (DATA / "cross_post_log.json").write_text(json.dumps(log, indent=2))
        return

    signals     = load_json("signal_tracker.json")
    social_last = load_json("social_latest.json")
    recs        = signals.get("recommendations", [])

    tweets  = [t.get("text", "") for t in social_last.get("tweets", [])
               if t.get("result", {}).get("status") == "queued" and t.get("text")]
    reddit  = [p.get("post", {}) for p in social_last.get("reddit", [])
               if p.get("result", {}).get("status") == "queued" and p.get("post")]

    posted_count = 0

    # Post first queued tweet if Twitter creds available
    for tweet_text in tweets[:1]:
        if already_posted(log, tweet_text, "twitter"):
            print("  Twitter: already posted this content — skipping")
            continue
        result = post_twitter(tweet_text)
        print(f"  Twitter: {result['status']}")
        log["posts"].append({
            "ts": ts, "platform": "twitter",
            "hash": content_hash(tweet_text),
            "text_preview": tweet_text[:80],
            "result": result,
        })
        if result["status"] == "posted":
            posted_count += 1

    # Post first queued Reddit post if Reddit creds available
    for rpost in reddit[:1]:
        sub   = rpost.get("subreddit", "SolarPunk")
        title = rpost.get("title", "")
        text  = rpost.get("text", "")
        if not title or already_posted(log, title, f"reddit/{sub}"):
            print(f"  Reddit r/{sub}: already posted — skipping")
            continue
        result = post_reddit(sub, title, text)
        print(f"  Reddit r/{sub}: {result['status']}")
        log["posts"].append({
            "ts": ts, "platform": f"reddit/{sub}",
            "hash": content_hash(title),
            "title_preview": title[:80],
            "result": result,
        })
        if result["status"] == "posted":
            posted_count += 1

    # Keep log bounded
    log["posts"] = log["posts"][-200:]
    log["last_run"] = ts
    log["total_posted"] = sum(1 for p in log["posts"] if p.get("result", {}).get("status") == "posted")
    (DATA / "cross_post_log.json").write_text(json.dumps(log, indent=2))

    has_creds = bool(X_API_KEY or REDDIT_CLIENT_ID)
    print(f"\n  Posted: {posted_count} | Log total: {log['total_posted']}")
    if not has_creds:
        print("  No social credentials set — posts queued for manual copy-paste")
        print("  Set X_API_KEY or REDDIT_CLIENT_ID in GitHub Secrets to auto-post")


if __name__ == "__main__":
    main()
