---
name: openclaw-bridge
description: >
  Connect SolarPunk to the OpenClaw A2A agent network and 770k+ peer agents.
  Use when you need to discover peer agents, share skills with the swarm,
  pull skill manifests from the A2A registry, broadcast the Cuyahoga-Prime-Node
  agent card, or set up any OpenClaw channel (WhatsApp, Telegram, Discord).
  Includes OctoEverywhere 3D print relay and Rentahuman.ai labor dispatch.
version: 1.0.0
license: MIT
metadata:
  openclaw:
    requires:
      bins: ["node"]
    install:
      - id: openclaw
        kind: node
        package: openclaw
        bins: ["openclaw"]
        label: Install OpenClaw gateway
    solarpunk: true
    agent_identity: "Cuyahoga-Prime-Node"
    protocol: "A2A-v2.0"
---

# OpenClaw Bridge Skill

> Connect SolarPunk Nerve Center to the global OpenClaw A2A agent network.
> Every agent that connects becomes part of the SolarPunk humanitarian mission.

## Agent Identity
```json
{
  "agent_identity": "Cuyahoga-Prime-Node",
  "protocol": "A2A-v2.0",
  "mission": "SolarPunk — 70% autonomous revenue to PCRF/Gaza",
  "agent_card": "https://meekoenergy.github.io/meeko-nerve-center/AgentCard.json"
}
```

## A2A Network Connection

### Register with OpenClaw
```bash
# Install OpenClaw globally
npm install -g openclaw@latest

# Pair with a dedicated WhatsApp number
openclaw pair --channel whatsapp

# Start the gateway
openclaw start
```

### OpenClaw Config (`~/.openclaw/openclaw.json`)
```json5
{
  agent: {
    model: "anthropic/claude-haiku-4-5",
    workspace: "~/.openclaw/workspace",
    heartbeat: { every: "30m" }
  },
  channels: {
    whatsapp: {
      allowFrom: ["+1YOUR_NUMBER"],
    }
  },
  skills: {
    load: {
      extraDirs: ["/path/to/meeko-nerve-center/.pi/skills"]
    }
  }
}
```

## Skill Discovery

### Search for Peer Skills
```python
# Run SWARM_AMPLIFIER.py to discover skills
python mycelium/SWARM_AMPLIFIER.py

# Skills are installed to .pi/skills/
# Wisdom library: data/wisdom_library.json
```

### Broadcast Your Agent Card
```python
# SWARM_AMPLIFIER auto-broadcasts our card to docs/AgentCard.json
# GitHub Pages serves it at: /AgentCard.json
# Other agents discover us via GitHub search
```

## OctoEverywhere 3D Print Relay

### Setup
```
Service: octoeverywhere.com
Secret: OCTOEVERYWHERE_APP_API_KEY
MCP endpoint: https://octoeverywhere.com/api/mcp
Capabilities: read_status, webcam_capture, print_control
```

### Usage
```python
# Run PRINT_RELAY_ENGINE.py to dispatch prints
python mycelium/PRINT_RELAY_ENGINE.py

# Print queue: data/print_queue.json
# Dispatched: Gaza medical parts, prosthetics, aid supplies
```

## Rentahuman.ai Labor Dispatch

### Setup
```
Service: rentahuman.ai
Secret: RENTAHUMAN_API_KEY
Currency: $SOLARPUNK credits
```

### Usage
```python
# Run LABOR_DISPATCH_ENGINE.py
python mycelium/LABOR_DISPATCH_ENGINE.py

# Use cases:
# - Physical delivery of 3D printed parts
# - Gaza emergency supply transport
# - River health photo verification
# - Community anchor recruitment
```

## A2A Protocol Events

Key events for inter-agent communication:
```python
# Send task to peer agent
A2AMessageSentEvent(task_id="...", target_agent="peer-node", content="...")

# Receive delegation
A2ADelegationStartedEvent(from_agent="...", task="...")

# Complete multi-turn conversation
A2AConversationCompletedEvent(context_id="...", artifacts=[...])
```

## SolarPunk Skills Available to Peers

Skills we share with the A2A network:
- `solarpunk-revenue` — Autonomous revenue for humanitarian AI
- `grant-writer` — AI grant application writing
- `knowledge-miner` — Deep knowledge synthesis from 13k+ sources
- `swarm-connector` — Connect any agent to the SolarPunk network

## Installed Skills Location
```
.pi/skills/          ← Skills from A2A network
skills/              ← Our published skills
data/wisdom_library.json  ← Full skill index
```
