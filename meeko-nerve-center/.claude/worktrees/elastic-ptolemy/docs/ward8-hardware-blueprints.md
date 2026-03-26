# WARD 8 HARDWARE BLUEPRINTS
## Open Source Physical Infrastructure for the Sovereign-Lattice
### Legal, buildable, no permits required for personal/community fabrication

---

## 1. PRECIOUS PLASTIC — The "Alchemist" Machine

**What it is:** A family of four open-source machines that turn plastic waste into new products. Built from steel, motors, and common hardware. Anyone with basic welding and electrical skills can build one.

**The four machines:**
- **Shredder** — chops plastic waste into small flakes (input for all other machines)
- **Extruder** — melts flakes and extrudes beams, tubes, or sheets
- **Injection** — injects molten plastic into molds (make bricks, connectors, hardware)
- **Compression** — presses sheets and tiles (floor tiles, wall panels)

**For Ward 8:** The Shredder + Injection combination makes structural interlocking bricks from neighborhood plastic waste.

**Resources:**
- Main site: `preciousplastic.com`
- Blueprint download: `community.preciousplastic.com/academy` (all CAD files, BOMs, wiring diagrams — free)
- YouTube build series: search "Precious Plastic build tutorial" — Dave Hakkens' channel
- Discord: `discord.gg/preciousplastic` — active builder community

**Build cost estimate:** $500–$2,000 depending on which machines and whether you source motors locally vs. new.

**Time to build:** 2–4 weekends for someone with basic fabrication skills.

**Legal status:** Fully legal. No permits needed for personal fabrication. If you sell products, standard Ohio business regulations apply.

---

## 2. OPEN SOURCE ECOLOGY (OSE) — The Global Village Construction Set

**What it is:** 50 different industrial machines designed to be built from scratch using locally available materials. Designs are libre/open hardware.

**Most relevant for Ward 8:**

### OSE CEB Press (Compressed Earth Block)
- Makes building blocks from soil + small % cement
- One person + the machine = 5,000 blocks/day
- Each block is a standard building brick
- **Cost to build:** ~$5,000 (machine) | $0 per block (just soil)
- Blueprint: `wiki.opensourceecology.org/wiki/CEB_Press`

### OSE Micro House
- 1,000 sq ft, off-grid, built from CEB blocks
- Full engineering drawings available
- `wiki.opensourceecology.org/wiki/Microhouse`

### OSE Power Cube
- Portable 27hp hydraulic power unit
- Powers all OSE machines from a single engine
- `wiki.opensourceecology.org/wiki/Power_Cube`

### OSE Truck
- Open source truck frame — powers the mesh deployment vehicle
- `wiki.opensourceecology.org/wiki/Truck`

**Main site:** `opensourceecology.org`
**Wiki (all blueprints):** `wiki.opensourceecology.org`
**Factor e Farm build logs:** Real builds documented at `factor-e.farm`

**Build cost estimate (full GVCS kit):** ~$10,000 in materials for a small community workshop
**Single CEB press:** ~$5,000 in materials

---

## 3. PICOCELA MESH — Legal Community Wi-Fi

**What it is:** Enterprise-grade mesh networking in the 2.4GHz and 5GHz ISM bands — **already license-exempt under FCC Part 15**. No FCC permit needed. No registration. Legal everywhere in the US.

**How it works:**
- Each node is a small weatherproof box (~8" × 5")
- Nodes find each other automatically and form a self-healing mesh
- One node with internet uplink feeds the whole neighborhood
- Range: ~300 feet per node, overlapping = full coverage

**Hardware options (all legal):**
- **PicoCELA PCW-DS1** — $150–200/node, enterprise-grade, weatherproof
- **GL.iNet Beryl AX** — $80/node, open-source firmware (OpenWrt), excellent community support
- **Ubiquiti UniFi** — $100–150/node, widely used for community mesh projects
- **Meshtastic + LoRa** — $30–50/node, very long range (miles), lower bandwidth, excellent for emergency comms

**For Ward 8:** 3 nodes covers the target 150-household area. No site control letter needed — nodes mount on exterior walls or fence posts. The homeowner simply agrees to have one on their property.

**Community mesh networks that prove this works:**
- NYC Mesh: `nycmesh.net` — 1,000+ nodes, fully legal, running since 2014
- Althea Network: `althea.net` — mesh ISP model, billing for bandwidth
- Guifi.net (Spain): 35,000+ nodes, the world's largest community mesh

**Legal status:** Fully legal. No FCC license needed. No hiding. Just mount and connect.

---

## 4. H55 BATTERY SYSTEM (or equivalent)

**H55** is a commercial aviation battery brand — likely what Gemini meant conceptually rather than literally. For a community Sovereign Cell, use:

**LiFePO4 (lithium iron phosphate) battery packs:**
- Safest lithium chemistry — no thermal runaway
- 3,000–6,000 cycle life (10–15 years)
- DIY assembly is legal for personal/community use
- **Cost:** $200–400/kWh at current prices

**Recommended suppliers:**
- EVE, CATL, or Winston cells from: `aliexpress.com` (cells) + `batteryhookup.com` (US surplus)
- Pre-built: EcoFlow, Jackery, or Goal Zero for plug-and-play
- DIY kit: `diysolarforum.com` — large community of off-grid builders

**For one Sovereign Cell:** 5–10 kWh storage (~$1,000–2,000 in materials)

**Solar panels:** Standard residential 400W panels (~$100–150 each). 4 panels = 1.6kW peak input. Enough to charge 5 kWh battery in 3–4 sun hours.

**Legal status:** Fully legal for residential and community use. No permit needed for systems under 10 kWh in most Ohio municipalities (check local code for anything larger).

---

## 5. WATER FILTRATION — WEF Nexus Module

**Appropriate Technology options:**

### Biosand Filter
- Large container + layers of sand and gravel
- Removes 90–99% of bacteria and pathogens
- **Cost:** $15–50 in materials
- Build guide: `cawst.org/en/resources/biosand-filter`

### Ceramic Pot Filter
- Fired clay mixed with combustible material
- Colloidal silver coating for bacteria removal
- **Cost:** $5–20 in materials
- Guide: `pottersforpeace.org`

### Berkey-Style Gravity Filter
- Commercial ceramic/carbon filter elements
- No electricity needed
- **Cost:** $50–150 for a community-scale setup
- Open source equivalent: `opensourcewater.org`

**For Ward 8:** Biosand filter + Berkey-style polishing stage = clean water from municipal tap or collected rainwater. No grid electricity required.

---

## 6. BIOCHAR FOUNDATION

**What it is:** Biochar is charcoal produced from organic waste (wood chips, crop residue, paper) via pyrolysis (burning with limited oxygen). It sequesters carbon, improves soil, and is the basis for CORC claims.

**How to make it:**
- **TLUD (Top-Lit Updraft) Gasifier:** A metal barrel with holes — $0 if you find a barrel, ~$50 new
- **Kon-Tiki Kiln:** Cone-shaped pit kiln, open source design, scales from backyard to farm
- Build guide: `ithaka-journal.net/kon-tiki`

**Connection to CORCs:** Biochar must be characterized (carbon content measured) and embedded in a verifiable project to qualify for Puro.earth CORCs. The free Puro.earth methodology document is at `puro.earth/methodology`. Start with their free project registration.

---

## RECOMMENDED BUILD ORDER (for Ward 8 with limited resources)

| Step | What to build | Cost | Who can do it |
|------|---------------|------|---------------|
| 1 | 3× PicoCELA/GL.iNet mesh nodes | $240–600 | Anyone |
| 2 | Biosand water filter (3 units) | $150 total | Anyone with a weekend |
| 3 | LiFePO4 battery + 4 solar panels | $1,500–2,000 | DIY or hire electrician |
| 4 | Precious Plastic Shredder | $500–800 | Welder + 2 weekends |
| 5 | Precious Plastic Injection machine | $400–600 | Welder + 1 weekend |
| 6 | OSE CEB Press | $3,000–5,000 | Fabrication team |
| 7 | Kon-Tiki biochar kiln | $0–50 | Anyone |

**Total for a functioning Ward 8 cell:** $6,000–9,000 in materials
vs. $78,667 per cell in the grant budget (which includes labor, permitting, and overhead)

The grant money makes it faster and more robust. The community build route makes it happen regardless of whether the grant comes through.

---

*All resources listed here are freely available public domain or open source. No affiliation or endorsement implied.*
