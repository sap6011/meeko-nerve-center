# Build a Local AI Agent with Ollama
### No API keys. No monthly fees. Your own AI running on your own machine.

---

**Price:** $1.00 · **A SolarPunk Guide** · 15% of every sale goes to Gaza via PCRF (EIN 93-1057665)

---

## Table of Contents

1. Why Local AI Changes Everything
2. Installing Ollama in 3 Minutes
3. Choosing Your Model: Mistral vs Llama 3 vs CodeLlama
4. Your First Python Agent in 20 Lines
5. Memory: Making Your Agent Remember Across Sessions
6. Giving Your Agent Tools: Web, Files, APIs
7. File System Agent: AI That Organizes Your Life
8. Email Agent: AI That Reads and Responds For You
9. Web Scraping Agent: AI That Browses While You Sleep
10. Multi-Agent Systems: Agents Talking to Each Other
11. Running 24/7: Systemd on Linux, Task Scheduler on Windows
12. Local + Cloud: Using Both Without Paying More

---

## 1. Why Local AI Changes Everything

Cloud AI charges you per token. A busy agent running every 15 minutes, processing documents, writing summaries, answering questions — that adds up to $50-200/month depending on the model.

Local AI costs electricity. On a modern laptop, running Ollama with a 7B parameter model uses about as much power as having Chrome open with 10 tabs. You already do that.

**What you gain with local AI:**

- **Privacy**: Your data never leaves your machine. Medical records, financial documents, personal journals — process them without sending them to anyone's server.
- **Speed**: No network round-trip. A local 7B model on decent hardware responds in 1-3 seconds. That's faster than most cloud API calls after you account for latency.
- **Cost**: After the initial download (4-8 GB for a good model), every inference is free. Run it a million times. No bill.
- **Availability**: No rate limits. No API outages. No "we've updated our terms of service." If your computer is on, your AI is available.
- **Control**: You pick the model. You control the system prompt. You decide what context it sees. No content filtering surprises mid-workflow.

**What you lose:**

- Raw intelligence. A local 7B model is not as capable as GPT-4 or Claude Opus. It makes more mistakes, misses nuance, and struggles with very complex reasoning.
- The fix: Use local for 90% of tasks (summarization, formatting, classification, simple generation) and cloud for the 10% that actually needs top-tier intelligence.

---

## 2. Installing Ollama in 3 Minutes

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from ollama.com. Run the installer. That's it.

**Verify it works:**
```bash
ollama run llama3.2
```

You'll see a chat prompt. Type "hello" and press Enter. If you get a response, you're done.

**Pull the models you'll need:**
```bash
ollama pull llama3.2          # General purpose, 3B, fast
ollama pull mistral           # Good at structured output, 7B
ollama pull codellama         # Code generation, 7B
ollama pull nomic-embed-text  # Embeddings for search/RAG
```

Each model downloads once and lives in `~/.ollama/models/`. Total disk: ~20 GB for all four.

---

## 3. Choosing Your Model: Mistral vs Llama 3 vs CodeLlama

| Task | Best Model | Why |
|------|-----------|-----|
| Chat, Q&A, summaries | llama3.2 (3B) | Fast, good at following instructions |
| JSON output, structured data | mistral (7B) | Best at consistent formatting |
| Code generation/review | codellama (7B) | Trained specifically on code |
| Document search (RAG) | nomic-embed-text | Turns text into vectors for similarity search |
| Complex reasoning | llama3.1 (70B) | Only if you have 48+ GB RAM |

**The practical advice**: Start with `llama3.2`. It's the smallest, fastest, and handles 80% of agent tasks well. Add `mistral` when you need reliable JSON output. Add `codellama` when your agent writes or reviews code.

**RAM requirements:**
- 3B model: 4 GB RAM (runs on any modern laptop)
- 7B model: 8 GB RAM (most laptops made after 2020)
- 13B model: 16 GB RAM
- 70B model: 48 GB RAM (desktop or server)

---

## 4. Your First Python Agent in 20 Lines

```python
#!/usr/bin/env python3
"""A complete local AI agent in 20 lines."""
import json, urllib.request

def ask(prompt, model="llama3.2"):
    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["response"]

# Use it
answer = ask("Summarize the benefits of local AI in 3 bullet points")
print(answer)
```

**What just happened:**
1. Ollama runs a local HTTP server on port 11434
2. Your Python script sends a POST request with the prompt
3. Ollama runs the model and returns the response
4. No API key. No internet. No cost.

**The chat endpoint** (for multi-turn conversations):
```python
def chat(messages, model="llama3.2"):
    data = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["message"]["content"]

response = chat([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's the capital of Ohio?"}
])
```

---

## 5. Memory: Making Your Agent Remember Across Sessions

A stateless agent forgets everything between calls. For useful agents, you need memory.

**Simple file-based memory:**
```python
from pathlib import Path
import json

MEMORY_FILE = Path("agent_memory.json")

def load_memory():
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return {"conversations": [], "facts": [], "preferences": {}}

def save_memory(memory):
    MEMORY_FILE.write_text(json.dumps(memory, indent=2))

def remember(fact):
    mem = load_memory()
    mem["facts"].append(fact)
    # Keep last 100 facts to prevent unbounded growth
    mem["facts"] = mem["facts"][-100:]
    save_memory(mem)

def recall(query, n=5):
    """Find the N most relevant memories (simple keyword match)."""
    mem = load_memory()
    words = query.lower().split()
    scored = []
    for fact in mem["facts"]:
        score = sum(1 for w in words if w in fact.lower())
        if score > 0:
            scored.append((score, fact))
    scored.sort(reverse=True)
    return [f for _, f in scored[:n]]
```

**Using memory in your agent:**
```python
def agent_respond(user_input):
    # Recall relevant memories
    context = recall(user_input)
    context_str = "\n".join(f"- {m}" for m in context) if context else "No relevant memories."

    prompt = f"""You have these memories:
{context_str}

User: {user_input}
Respond helpfully, using your memories when relevant."""

    response = ask(prompt)

    # Remember the interaction
    remember(f"User asked: {user_input[:100]}")
    remember(f"I answered about: {user_input[:50]}")

    return response
```

**Upgrading to vector memory** (for better recall):
```python
def embed(text, model="nomic-embed-text"):
    data = json.dumps({"model": model, "prompt": text}).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/embeddings",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["embedding"]

def cosine_sim(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na = sum(x*x for x in a) ** 0.5
    nb = sum(x*x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0
```

With embeddings, your agent finds semantically similar memories, not just keyword matches. "What's the weather?" retrieves memories about "temperature forecast" even though they share no words.

---

## 6. Giving Your Agent Tools: Web, Files, APIs

An agent with tools is dramatically more useful than one without. Here's the pattern:

```python
TOOLS = {
    "read_file": lambda path: Path(path).read_text()[:5000],
    "write_file": lambda path, content: Path(path).write_text(content),
    "web_get": lambda url: urllib.request.urlopen(url).read().decode()[:5000],
    "list_files": lambda dir: "\n".join(str(p) for p in Path(dir).iterdir()),
    "run_command": lambda cmd: subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout[:3000],
}

def agent_with_tools(task):
    tool_desc = """Available tools:
    - read_file(path): Read a file's contents
    - write_file(path, content): Write content to a file
    - web_get(url): Fetch a URL's contents
    - list_files(dir): List files in a directory
    - run_command(cmd): Run a shell command

    To use a tool, respond with: TOOL: tool_name(args)
    To give your final answer: ANSWER: your response"""

    messages = [
        {"role": "system", "content": f"You are an agent with tools.\n{tool_desc}"},
        {"role": "user", "content": task}
    ]

    for _ in range(5):  # Max 5 tool calls per task
        response = chat(messages)

        if response.startswith("ANSWER:"):
            return response[7:].strip()

        if response.startswith("TOOL:"):
            # Parse and execute tool call
            tool_call = response[5:].strip()
            try:
                result = eval(tool_call, {"__builtins__": {}}, TOOLS)
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Tool result: {result}"})
            except Exception as e:
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Tool error: {e}"})
        else:
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": "Please use TOOL: or ANSWER: format."})

    return "Agent ran out of steps."
```

**Security note**: The `eval()` above is for demonstration. In production, parse the tool name and arguments explicitly — never eval untrusted input.

---

## 7. File System Agent: AI That Organizes Your Life

```python
def organize_downloads():
    """AI-powered file organizer for your Downloads folder."""
    downloads = Path.home() / "Downloads"
    files = [f for f in downloads.iterdir() if f.is_file()]

    if not files:
        print("Downloads folder is empty")
        return

    # Ask the AI to categorize each file
    file_list = "\n".join(f.name for f in files[:50])
    categories = ask(f"""Categorize these files into folders.
Return JSON: {{"filename": "category"}}
Categories: documents, images, videos, code, archives, installers, other

Files:
{file_list}""", model="mistral")

    try:
        mapping = json.loads(categories)
    except json.JSONDecodeError:
        print("AI returned invalid JSON, skipping")
        return

    for filename, category in mapping.items():
        src = downloads / filename
        dst = downloads / category
        if src.exists():
            dst.mkdir(exist_ok=True)
            src.rename(dst / filename)
            print(f"  {filename} -> {category}/")
```

**Daily summary agent:**
```python
def daily_summary():
    """Summarize today's file activity."""
    from datetime import datetime, timedelta
    import os

    today = datetime.now().date()
    recent = []

    for root, dirs, files in os.walk(Path.home() / "Documents"):
        for f in files:
            path = Path(root) / f
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime).date()
                if mtime == today:
                    recent.append(str(path))
            except:
                pass

    if recent:
        summary = ask(f"Summarize what I worked on today based on these modified files:\n" +
                      "\n".join(recent[:30]))
        print(f"Today's summary:\n{summary}")
```

---

## 8. Email Agent: AI That Reads and Responds For You

```python
import imaplib, email

def check_email(addr, password, imap_server="imap.gmail.com"):
    """Read unread emails, AI-summarize, draft responses."""
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(addr, password)
    mail.select("inbox")

    _, msgs = mail.search(None, "UNSEEN")
    summaries = []

    for num in msgs[0].split()[:10]:  # Max 10 emails
        _, data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        subject = msg["subject"] or "(no subject)"
        sender = msg["from"] or "(unknown)"
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="replace")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="replace")

        # AI summarize
        summary = ask(f"Summarize this email in 1-2 sentences:\nFrom: {sender}\nSubject: {subject}\nBody: {body[:1000]}")

        # AI draft response
        draft = ask(f"Draft a brief, professional response to this email:\nFrom: {sender}\nSubject: {subject}\nBody: {body[:1000]}")

        summaries.append({
            "from": sender,
            "subject": subject,
            "summary": summary,
            "draft_response": draft
        })

    mail.logout()
    return summaries
```

**Important**: Use an App Password for Gmail (not your real password). Go to myaccount.google.com > Security > 2-Step Verification > App Passwords.

---

## 9. Web Scraping Agent: AI That Browses While You Sleep

```python
import urllib.request
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer"):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer"):
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text:
                self.text.append(text)

def scrape(url):
    """Fetch a URL and extract readable text."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; SolarPunk-Agent/1.0)"
    })
    html = urllib.request.urlopen(req, timeout=10).read().decode(errors="replace")
    parser = TextExtractor()
    parser.feed(html)
    return " ".join(parser.text)[:5000]

def research_agent(topic):
    """Research a topic by scraping and summarizing."""
    # Scrape a few sources
    sources = [
        f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
    ]

    findings = []
    for url in sources:
        try:
            text = scrape(url)
            summary = ask(f"Extract the 3 most important facts about '{topic}' from this text:\n{text}")
            findings.append(summary)
        except:
            pass

    # Synthesize
    combined = "\n\n".join(findings)
    final = ask(f"Write a comprehensive 3-paragraph summary about '{topic}' based on these findings:\n{combined}")
    return final
```

---

## 10. Multi-Agent Systems: Agents Talking to Each Other

The real power comes when agents collaborate. Here's the SolarPunk pattern:

```python
def multi_agent_task(task):
    """Three agents collaborate: Planner, Worker, Reviewer."""

    # Agent 1: Planner breaks down the task
    plan = ask(f"Break this task into 3-5 concrete steps:\n{task}", model="mistral")

    # Agent 2: Worker executes each step
    results = []
    for step in plan.split("\n"):
        if step.strip():
            result = ask(f"Execute this step and return the output:\n{step}", model="llama3.2")
            results.append(result)

    # Agent 3: Reviewer checks quality
    all_work = "\n\n".join(results)
    review = ask(f"""Review this work for quality and completeness.
Task: {task}
Plan: {plan}
Results:
{all_work}

If there are issues, describe them. If it's good, say APPROVED.""", model="mistral")

    return {
        "plan": plan,
        "results": results,
        "review": review,
        "approved": "APPROVED" in review.upper()
    }
```

**The SolarPunk spoke-and-hub pattern** (how 242 engines coordinate):
```python
# Each agent writes to a shared data/ directory
# No agent calls another directly
# The data files ARE the communication layer

# Agent A writes its output
(DATA / "agent_a_output.json").write_text(json.dumps(result))

# Agent B reads Agent A's output (whenever it runs, even hours later)
if (DATA / "agent_a_output.json").exists():
    input_data = json.loads((DATA / "agent_a_output.json").read_text())
```

This is simpler than message queues, more resilient than direct calls, and completely inspectable — just read the JSON files.

---

## 11. Running 24/7: Systemd on Linux, Task Scheduler on Windows

**Linux (systemd):**

Create `/etc/systemd/system/my-agent.service`:
```ini
[Unit]
Description=Local AI Agent
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/my-agent
ExecStart=/usr/bin/python3 agent.py
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable my-agent
sudo systemctl start my-agent
```

Your agent runs every 5 minutes (RestartSec=300), forever.

**Windows (Task Scheduler):**

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\Users\you\agent\agent.py" -WorkingDirectory "C:\Users\you\agent"
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 15) -At "12:00 AM" -Once
Register-ScheduledTask -TaskName "LocalAIAgent" -Action $action -Trigger $trigger -RunLevel Highest
```

**macOS (launchd):**

Create `~/Library/LaunchAgents/com.solarpunk.agent.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.solarpunk.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/you/agent/agent.py</string>
    </array>
    <key>StartInterval</key>
    <integer>900</integer>
    <key>WorkingDirectory</key>
    <string>/Users/you/agent</string>
</dict>
</plist>
```

---

## 12. Local + Cloud: Using Both Without Paying More

The optimal setup uses local AI for routine tasks and cloud AI only when you need the best intelligence:

```python
def smart_ask(prompt, complexity="auto"):
    """Route to local or cloud based on task complexity."""
    if complexity == "auto":
        # Quick heuristic: long prompts or reasoning tasks go to cloud
        needs_cloud = (
            len(prompt) > 2000 or
            any(w in prompt.lower() for w in ["analyze", "reason", "complex", "compare"])
        )
    else:
        needs_cloud = complexity == "high"

    if needs_cloud and os.environ.get("ANTHROPIC_API_KEY"):
        return ask_cloud(prompt)  # Claude, GPT-4, etc.
    else:
        return ask(prompt)  # Local Ollama

def ask_cloud(prompt):
    """Fall back to cloud AI for complex tasks."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ask(prompt)  # Graceful fallback to local

    data = json.dumps({
        "model": "claude-sonnet-4-6-20250514",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["content"][0]["text"]
```

**Cost comparison:**
- Pure cloud (all tasks via API): ~$50-200/month
- Pure local (7B model): $0/month + electricity
- Hybrid (90% local, 10% cloud): ~$5-15/month

The hybrid approach gives you 95% of the capability at 10% of the cost.

---

## About SolarPunk

This guide was written by a human who builds autonomous AI systems and the AI tools that help maintain them. Everything described here is real, tested, and running in production.

15% of every sale goes to Palestinian children via PCRF.
PCRF EIN: 93-1057665 · 4-star Charity Navigator · Operating in Gaza since 1991

**Fork it:** github.com/meekotharaccoon-cell/meeko-nerve-center
**Store:** meekotharaccoon-cell.github.io/meeko-nerve-center/store.html
**Donate directly:** pcrf.net

---
*Built autonomously. Funded for Gaza. Running forever.*
