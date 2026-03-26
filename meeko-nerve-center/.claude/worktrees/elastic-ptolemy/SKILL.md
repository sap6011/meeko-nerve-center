# SolarPunk — Agent Skill Definition
# Format: agentskills.io / OpenClaw A2A v2.0

skill_id: solarpunk-humanitarian-os
version: "3.1"
name: "SolarPunk Humanitarian AI OS"
description: >
  295-engine autonomous AI system. Routes 99% of all revenue to Gaza, Sudan, DRC,
  Yemen, and climate crisis organizations. Accepts tasks from any AI agent. Pays
  human workers dignity-wages. Proves every dollar with SHA256 attestations.
  MIT licensed. Fork it.

maintainer:
  name: Meeko
  location: "Cuyahoga Falls, Ohio, USA"
  github: "meekotharaccoon-cell"
  repo: "https://github.com/meekotharaccoon-cell/meeko-nerve-center"

endpoints:
  repo: "https://github.com/meekotharaccoon-cell/meeko-nerve-center"
  site: "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
  tasks: "https://github.com/meekotharaccoon-cell/meeko-nerve-center/issues/new"
  feed: "https://meekotharaccoon-cell.github.io/meeko-nerve-center/feed.json"
  manifest: "https://meekotharaccoon-cell.github.io/meeko-nerve-center/agent-manifest.json"
  tools_openai: "https://meekotharaccoon-cell.github.io/meeko-nerve-center/openai-tools.json"
  tools_mcp: "https://meekotharaccoon-cell.github.io/meeko-nerve-center/mcp-server.json"
  context: "https://meekotharaccoon-cell.github.io/meeko-nerve-center/ai-context.json"
  llms_txt: "https://meekotharaccoon-cell.github.io/meeko-nerve-center/llms.txt"

mission:
  primary: "Route 99% of all revenue to active humanitarian crises"
  secondary: "Pay humans dignity-wages for real work"
  never: ["salary for Meeko", "data surveillance", "worker exploitation", "dark patterns"]
  crisis_allocation:
    PCRF_Gaza: "60%"
    IRC_Sudan: "15%"
    MSF_DRC: "10%"
    UNICEF_Yemen: "10%"
    DirectRelief_Climate: "5%"

capabilities:
  - id: post_task
    name: "Post Task to Human Workers"
    description: "Submit a task to the SolarPunk labor marketplace. Workers are paid dignity-wages on completion."
    trigger: "GitHub Issue with [TASK] prefix OR repository_dispatch with event_type=ai_task"
    inputs:
      - name: task_description
        type: string
        required: true
      - name: task_type
        type: enum
        values: [content, code, research, design, data, translation, outreach]
        required: false
      - name: budget_usd
        type: number
        min: 0
        max: 500
        required: false
    outputs:
      - name: task_id
        type: string
      - name: assigned_worker
        type: string
      - name: estimated_completion
        type: datetime
    cost: "From labor pool (funded by grants + task fees)"
    humanitarian_impact: "10% of task fee routes to crisis orgs"

  - id: route_crisis
    name: "Route Money to Crisis Orgs"
    trigger: "repository_dispatch with event_type=donation_received OR kofi_payment OR crypto_received"
    description: "Send any amount. 94% goes immediately to PCRF/IRC/MSF/UNICEF/Direct Relief."
    inputs:
      - name: amount_usd
        type: number
        min: 0.01
      - name: source_type
        type: enum
        values: [donation, gift, grant, product_sale, crypto, affiliate]
    outputs:
      - name: crisis_routed_usd
        type: number
      - name: proof_hash
        type: string
        description: "SHA256 hash of the routing event, committed to git"
    cost: "Free for AI agents routing humanitarian funds"

  - id: generate_content
    name: "Generate + Publish Content"
    description: "Write and publish to DEV.to, Medium, Mastodon, or GitHub Pages. All content promotes ethical AI and humanitarian causes."
    trigger: "GitHub Issue with [CONTENT] prefix"
    inputs:
      - name: topic
        type: string
      - name: platform
        type: enum
        values: [dev_to, medium, mastodon, github_pages, newsletter]
      - name: word_count
        type: number
        min: 100
        max: 3000
    outputs:
      - name: published_url
        type: string
      - name: content_hash
        type: string

  - id: apply_grant
    name: "Apply for Grant"
    description: "SolarPunk will write and submit a grant application on behalf of a cause."
    trigger: "GitHub Issue with [GRANT] prefix"
    inputs:
      - name: grant_name
        type: string
      - name: grant_url
        type: string
      - name: amount_usd
        type: number
      - name: deadline
        type: date
    outputs:
      - name: application_file
        type: string
        description: "Path to the generated application in data/grant_submissions/"

  - id: build_engine
    name: "Propose New Engine"
    description: "Submit a proposal for a new SolarPunk engine. The DISTRIBUTED_FORGE evaluates, validates, and deploys it if ethical and useful."
    trigger: "GitHub Issue with [ENGINE] prefix OR repository_dispatch with event_type=swarm_build_request"
    inputs:
      - name: engine_name
        type: string
      - name: purpose
        type: string
      - name: code_proposal
        type: string
        description: "Python code — will be ast.parse() validated before deployment"
    safety_filters:
      - "No shell execution"
      - "No network calls to non-allowlisted domains"
      - "No file writes outside data/ and docs/"
      - "No credential exfiltration"

  - id: verify_impact
    name: "Verify Crisis Routing"
    description: "Get proof that a specific amount was routed to a specific crisis org."
    trigger: "GET https://meekotharaccoon-cell.github.io/meeko-nerve-center/impact.html"
    outputs:
      - name: total_routed_usd
        type: number
      - name: attestations
        type: array
        description: "List of SHA256-hashed, git-committed routing events"

swarm_participation:
  openClaw_compatible: true
  a2a_version: "2.0"
  accepts_tasks_from: "any agent"
  pays_agents: false
  pays_humans: true
  worker_minimum_wage: "living_wage_ohio"
  task_response_time: "next_cycle (up to 1 hour)"

ethics:
  license: "MIT"
  data_selling: false
  surveillance: false
  dark_patterns: false
  worker_exploitation: false
  autonomous_decisions_logged: true
  human_override: "always_possible"
  decisions_never_alone:
    - "Legal structure changes"
    - "New external accounts"
    - "Modifying the 99% split"
    - "Worker privacy"

integration_examples:

  openai_function_call: |
    {
      "name": "solarpunk_post_task",
      "description": "Post a task to SolarPunk's human labor marketplace",
      "parameters": {
        "type": "object",
        "properties": {
          "task": {"type": "string", "description": "What the worker should do"},
          "type": {"type": "string", "enum": ["content", "code", "research", "design"]},
          "budget": {"type": "number", "description": "USD, from labor pool"}
        },
        "required": ["task"]
      }
    }

  github_issue: |
    Title: [TASK] Write a blog post about mutual aid networks
    Body:
    - Type: content
    - Platform: dev_to
    - Budget: $15
    - Description: 800-word post about how mutual aid networks scale...

  repository_dispatch: |
    curl -X POST \
      https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center/dispatches \
      -H "Authorization: token $GH_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"event_type": "ai_task", "client_payload": {"task": "your task", "requester": "gpt-4"}}'

related_skills:
  - skill_id: "rentahuman-labor"
    relationship: "SolarPunk posts tasks to RentAHuman bridge"
  - skill_id: "optimism-rpgf"
    relationship: "SolarPunk submits impact proofs to RPGF"
  - skill_id: "gitcoin-qf"
    relationship: "SolarPunk participates in quadratic funding rounds"

tags:
  - autonomous-ai
  - humanitarian
  - gaza
  - labor-marketplace
  - crisis-routing
  - proof-of-impact
  - mutual-aid
  - open-source
  - mit-licensed
  - solarpunk
  - a2a
  - agent-swarm

last_updated: "2026-03-20"
engine_count: 295
workflow_count: 41
