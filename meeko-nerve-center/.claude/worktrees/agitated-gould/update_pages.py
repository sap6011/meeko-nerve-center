#!/usr/bin/env python3
"""Update all pages with new project count and nav links."""
from pathlib import Path

# ── synthesis.html ────────────────────────────────────────────
syn = Path("docs/synthesis.html").read_text(encoding="utf-8")
syn = syn.replace('synthesis-count">12', 'synthesis-count">13')
syn = syn.replace('projects-count">24', 'projects-count">32')
# Add mesh/replicate to nav if missing
if "mesh.html" not in syn:
    syn = syn.replace(
        '<a href="map.html">🗺️ Map</a>',
        '<a href="mesh.html">📡 $1.50 Internet</a>\n  <a href="replicate.html">🔬 Replicate</a>\n  <a href="map.html">🗺️ Map</a>'
    )
Path("docs/synthesis.html").write_text(syn, encoding="utf-8")
print("synthesis.html: 13 models, 32 projects")

# ── solarpunk-movement.html ───────────────────────────────────
mov = Path("docs/solarpunk-movement.html").read_text(encoding="utf-8")
mov = mov.replace("24 verified projects", "32 verified projects")
mov = mov.replace(">24 verified", ">32 verified")
if "mesh.html" not in mov:
    mov = mov.replace(
        '<a href="map.html">',
        '<a href="mesh.html">📡 $1.50 Internet</a>\n  <a href="replicate.html">🔬 Replicate</a>\n  <a href="map.html">'
    )
Path("docs/solarpunk-movement.html").write_text(mov, encoding="utf-8")
print("solarpunk-movement.html: updated")

# ── map.html — add 7 new pins ─────────────────────────────────
map_h = Path("docs/map.html").read_text(encoding="utf-8")

if "'guifi-net'" not in map_h:
    new_pins = """  'guifi-net': {
    tag: 'Community Mesh · Spain',
    name: 'Guifi.net — 42,000-Node Network',
    loc: '📍 Catalonia, Spain',
    desc: 'The largest community-owned telecoms network in the world. 42,000 nodes. Zero cost for contributing members. Procomuns license: use it, extend it, give back.',
    metrics: [['42,000','Nodes'],['3','Countries'],['2004','Since'],['Free','For contributors']],
    steps: ['Register as cooperative','Adopt Wireless Commons License','Start with 10 node owners','Flash LibreMesh firmware — free','Add solar to remote nodes'],
    links: [['Guifi.net','https://guifi.net'],['Replicate','replicate.html']],
    cat: 'all digital',
    coords: [41.9, 2.25]
  },
  'altermundi': {
    tag: 'Community Mesh · Argentina',
    name: 'AlterMundi — Rural Networks',
    loc: '📍 Córdoba, Argentina',
    desc: 'LibreMesh firmware used by 100+ communities in 40 countries. $2/month. Solar nodes extend to off-grid farmsteads. Email redes@altermundi.net for free guide.',
    metrics: [['100+','Communities'],['40','Countries'],['$2','Per month'],['LibreMesh','Open-source firmware']],
    steps: ['Download LibreMesh','Form 5+ household assembly','Flash routers ($30-150)','Install solar','Email redes@altermundi.net'],
    links: [['AlterMundi','https://altermundi.net'],['LibreMesh','https://libremesh.org']],
    cat: 'all digital',
    coords: [-31.4, -64.2]
  },
  'rhizomatica': {
    tag: 'Indigenous Cellular · Mexico',
    name: 'Rhizomatica / TIC',
    loc: '📍 Sierra Juárez, Oaxaca, Mexico',
    desc: '75 indigenous communities own their cellular networks for $1.50/month. 95% cheaper than commercial. First indigenous spectrum licenses in Mexico. Solar base stations.',
    metrics: [['$1.50','Per month'],['75','Communities'],['95%','Cheaper'],['2013','Since']],
    steps: ['Form telecom cooperative','Apply for community spectrum license','Install OpenBTS ($3,000-8,000)','Add 200W solar + 100Ah battery','Email info@rhizomatica.org'],
    links: [['Rhizomatica','https://rhizomatica.org'],['Replicate','replicate.html']],
    cat: 'all digital indigenous',
    coords: [17.1, -96.7]
  },
  'air-jaldi': {
    tag: 'Rural WiFi · India',
    name: 'AirJaldi — Mountain WiFi',
    loc: '📍 Himachal Pradesh, India',
    desc: '200+ Himalayan villages. 250,000 people online at $3/month. Directional antennas bridge 40-80km mountain passes. Solar relay stations. 7 states.',
    metrics: [['250K','People'],['$3','Per month'],['200+','Villages'],['80km','Max link distance']],
    steps: ['Survey with Google Earth','Use Ubiquiti for long links','Solar power relay stations','Form rural cooperative','Contact info@jaldi.org.in'],
    links: [['AirJaldi','https://airjaldi.com'],['Replicate','replicate.html']],
    cat: 'all digital',
    coords: [32.2, 76.3]
  },
  'fantsuam': {
    tag: 'Community ISP · Nigeria',
    name: 'Fantsuam Foundation',
    loc: '📍 Kafanchan, Kaduna State, Nigeria',
    desc: "Nigeria's first rural ISP. 100% solar. 5,000+ women trained in ICT. The network funds the training. Zero fossil fuel dependency since 2005.",
    metrics: [['5,000','Women trained'],['20','Communities'],['100%','Solar'],['2005','Since']],
    steps: ['Register as NGO','Install 3-5kW solar first','Set up tower + LibreRouter mesh','Apply for national ISP license','Pair internet with training'],
    links: [['Fantsuam','https://fantsuam.net'],['APC','https://apc.org']],
    cat: 'all digital',
    coords: [9.58, 8.29]
  },
  'kopernik': {
    tag: 'Solar Home Systems · Indonesia',
    name: 'Kopernik — Last Mile Solar',
    loc: '📍 Indonesia + East Timor',
    desc: '240,000 solar units to isolated communities via women entrepreneurs. 1.2M+ people reached. Women ARE the distribution network.',
    metrics: [['240K','Solar units'],['1.2M','People reached'],['3','Countries'],['Women','Led']],
    steps: ['Map off-grid communities','Recruit women distributors','Source solar wholesale','Offer PAYG mobile money credit','Contact kopernik.info/partner'],
    links: [['Kopernik','https://kopernik.info']],
    cat: 'all solar',
    coords: [-8.34, 115.09]
  },
  'nyc-mesh': {
    tag: 'Community Mesh · USA',
    name: 'NYC Mesh',
    loc: '📍 New York City, USA',
    desc: '1,400 nodes across all 5 boroughs. Free if you cannot pay. $20/month if you can. Survived Hurricane Sandy. Solidarity pricing: ability to pay never determines access.',
    metrics: [['1,400','Nodes'],['$0','If you need it'],['500+','Buildings'],['2014','Since']],
    steps: ['Form nonprofit','Install supernodes on tall buildings','Ethernet from rooftop to apartments','Adopt solidarity pricing','Copy docs.nycmesh.net openly'],
    links: [['NYC Mesh','https://nycmesh.net'],['Docs','https://docs.nycmesh.net']],
    cat: 'all digital',
    coords: [40.7128, -74.006]
  },
"""
    # Insert before the 'inethi' entry
    map_h = map_h.replace("  'inethi': {", new_pins + "  'inethi': {")

# Update project count in map stats bar if present
map_h = map_h.replace(">24 projects<", ">32 projects<")
map_h = map_h.replace('"24"', '"32"')
map_h = map_h.replace("'24'", "'32'")

# Add Replicate to map nav if missing
if "replicate.html" not in map_h:
    map_h = map_h.replace(
        '<a href="start-here.html">',
        '<a href="replicate.html">🔬 Replicate</a>\n  <a href="start-here.html">'
    )

Path("docs/map.html").write_text(map_h, encoding="utf-8")
print("map.html: 7 new pins added, nav updated")

# ── start-here.html ───────────────────────────────────────────
sh = Path("docs/start-here.html").read_text(encoding="utf-8")
if "replicate.html" not in sh:
    sh = sh.replace(
        '<a href="mesh.html">',
        '<a href="replicate.html">🔬 Replicate</a>\n  <a href="mesh.html">'
    )
    Path("docs/start-here.html").write_text(sh, encoding="utf-8")
    print("start-here.html: nav updated")

print("\nAll pages updated.")
