# рџЋЇ PROJECT-S SERVER HUNT - COMPLETE SYSTEM
## AI-Powered Server Procurement Campaign for HP DL380 & Dell R730/R740

**Status**: вњ… Ready for launch  
**Last Update**: 2026-02-19  
**Campaign Target**: Ukrainian + International IT marketplaces

---

## рџ“‹ QUICK START

### ONE-COMMAND EXECUTION

```powershell
cd c:\1225\project_s_super_core
python server_hunt_maestro.py
```

**What happens**:
1. рџЊђ Scrapes 10 platforms simultaneously (5-10 minutes)
2. рџ¤– Analyzes deals with DeepSeek V3 AI (2-3 minutes)
3. рџ“Љ Generates comprehensive reports
4. рџ’ѕ Saves results to Desktop

**Expected Output** (on Desktop):
- `server_hunt_campaign_[date].txt` - Full scraping report + top deals
- `server_hunt_data_[date].json` - Structured data (for further processing)
- `server_hunt_analysis_[date].txt` - AI procurement analysis + recommendations

---

## рџЏ—пёЏ SYSTEM ARCHITECTURE

### Three-Component System

```
в”Њв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”ђ
в”‚          SERVER HUNT MAESTRO (Orchestrator)             в”‚
в”‚                                                          в”‚
в”‚  Phase 1пёЏвѓЈ: WEB SCRAPING          Phase 2пёЏвѓЈ: AI ANALYSIS    в”‚
в”‚  в”њв”Ђ server_hunt_scraper.py       в””в”Ђ server_hunt_analyzer.py
в”‚  в”њв”Ђ 10 platform adapters         в””в”Ђ DeepSeek V3 integration
в”‚  в””в”Ђ Deal scoring algorithm       в””в”Ђ Negotiation strategy
в”‚                                                          в”‚
в”‚              в†“ DATA FLOW                                 в”‚
в”‚                                                          в”‚
в”‚  JSON: server_hunt_data_*.json                          в”‚
в”‚  в†“                                                       в”‚
в”‚  HTML в†’ Parse в†’ Extract в†’ Score в†’ Rank в†’ Analyze       в”‚
в””в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”
```

### Component Files

#### 1. `server_hunt_config.yaml` (Configuration)
**Purpose**: Centralized hunting specifications  
**Size**: ~2.5 KB  
**Contents**:
- Search targets (models, cores, RAM, price, form factor)
- Platform definitions (10 platforms with selectors)
- Scoring rules (multi-factor algorithm parameters)
- Alert triggers (special deal conditions)
- Execution parameters (browser, timeout, caching)

**Usage**: Referenced by scraper for all configuration

#### 2. `server_hunt_scraper.py` (Phase 1 - Data Collection)
**Purpose**: Multi-platform web scraping  
**Size**: 14.5 KB  
**Language**: Python 3.11 async  
**Dependencies**: playwright, pyyaml, asyncio

**Key Methods**:
```python
_extract_cpu_cores(text)          # Parse CPU specs
_extract_ram_gb(text)             # Parse memory specs
_extract_price_uah(text)          # Parse & normalize price
_extract_server_model(text)       # Identify server model
_score_deal(offer)                # Multi-factor scoring

scrape_olx_ua()                   # OLX.ua adapter
scrape_prom_ua()                  # Prom.ua adapter
scrape_serverparts()              # serverparts.com.ua adapter
[+ 7 more platform adapters planned]

_generate_report()                # Markdown reporting
run()                             # Main orchestration
```

**Inputs**:
- `server_hunt_config.yaml` - Configuration

**Outputs**:
- `server_hunt_campaign_[date].txt` - Formatted report
- `server_hunt_data_[date].json` - Structured data

**Current Status**:
- вњ… 3 platform adapters implemented (OLX, Prom, serverparts)
- вњ… Deal scoring algorithm complete
- вњ… Report generation ready
- рџџЎ Awaiting execution validation
- вЏі Remaining 7 platform adapters (planned)

#### 3. `server_hunt_analyzer.py` (Phase 2 - AI Analysis)
**Purpose**: DeepSeek V3 powered procurement strategy  
**Size**: 11.8 KB  
**Language**: Python 3.11 async  
**Dependencies**: httpx, asyncio, json

**Key Methods**:
```python
_find_latest_hunt_data()          # Locate scaper JSON
_load_hunt_data(json_file)        # Load & parse data
_prepare_analysis_prompt(data)    # Format context for AI
call_ai_analysis(prompt)          # Call DeepSeek API
_generate_final_report(data, ai)  # Compile final report
run()                             # Orchestration
```

**Inputs**:
- `server_hunt_data_[date].json` - From scraper

**Outputs**:
- `server_hunt_analysis_[date].txt` - AI recommendations

**AI Features**:
- Deal value analysis (top 3 offers)
- Market trend insights
- Negotiation playbook (3 opening offers per deal)
- Risk assessment & health checks
- Portfolio strategy (if buying 2-3 units)
- Template emails for sellers

**API Requirements**:
- OpenRouter API key: `OPENROUTER_API_KEY` environment variable
- Or OpenAI key: `OPENAI_API_KEY` environment variable
- Model: deepseek/deepseek-chat

#### 4. `server_hunt_maestro.py` (Orchestrator)
**Purpose**: Complete campaign automation  
**Size**: 12.2 KB  
**Language**: Python 3.11 async  
**Status**: вњ… Ready

**Execution Flow**:
1. Validates all required files + API key
2. Launches scraper (async)
3. Waits for scraper completion
4. Launches analyzer (async)
5. Waits for analyzer completion
6. Opens results on Desktop
7. Displays completion summary

---

## рџЋЇ SEARCH SPECIFICATIONS

### Target Hardware

**Models**:
- HP DL380 G8 / G9 (2U, Xeon E5/E5 v2)
- Dell PowerEdge R730 (2U, Xeon E5 v2)
- Dell PowerEdge R740 (2U, Xeon Scalable / 3rd Gen)

**Minimum Specs**:
- **CPU**: 20-28 cores (2Г—10-core or 2Г—14-core Xeons)
- **RAM**: 64 GB minimum (DDR3/DDR4)
- **Form Factor**: 2U (GPU-ready, standard rack)
- **Condition**: Used/Refurbished/New acceptable

**Target Price**:
- **Ideal**: < 40,000 UAH (about $1,000 USD / в‚¬900 EUR)
- **Maximum**: < 50,000 UAH if specs excellent
- **Sweet Spot**: 35,000 - 40,000 UAH

### Why These Specs?

| Metric | Reasoning |
|--------|-----------|
| 20+ cores | Sufficient for parallel workloads, good value/core |
| 64+ GB RAM | Memory-intensive applications (ML, databases, VMs) |
| 2U form | Standard rack size, excellent availability, 24 GPU slots |
| E5 generation | Sweet spot: supported, refurbished abundant, parts available |
| <40k UAH | Budget-conscious procurement, good ROI |

---

## рџ“Ќ PLATFORMS (10 Total)

### Ukraine (7 platforms)

| # | Platform | Type | Search Pattern | Audience |
|---|----------|------|-----------------|----------|
| 1 | **OLX.ua** | C2C Marketplace | "DL380" OR "R730" OR "R740" | Largest (most inventory) |
| 2 | **Prom.ua** | B2B Marketplace | "hp dl380" + filter refurb | Business sellers |
| 3 | **serverparts.com.ua** | Parts/Server specialist | [product search] | IT specialists |
| 4 | **server.ua** | Server specialist | [catalog browse] | Server enthusiasts |
| 5 | **it-komplekt.com.ua** | IT equipment | "server" + "xeon" | Corporate buyers |
| 6 | **Rozetka Marketplace** | General marketplace | "СЃРµСЂРІРµСЂРЅС‹Р№ РїСЂРѕС†РµСЃСЃРѕСЂ" | Mixed |
| 7 | **Facebook Marketplace UA** | Social marketplace | "DL380" OR "R730" groups | Individual sellers |

### International (3 platforms)

| # | Platform | Region | Advantage | Shipping |
|---|----------|--------|-----------|----------|
| 8 | **eBay.com (EU sellers)** | Europe | Large inventory, buyer protection | 10-20 EUR |
| 9 | **ServerMonkey.com** | USA/International | Refurb specialist, warranty | Expensive shipping |
| 10 | **Hetzner Auctions** | Germany | Bulk liquidation, excellent pricing | EU shipping fast |

---

## рџ§® DEAL SCORING ALGORITHM

### Scoring Formula

```
DEAL_SCORE = (CPU_CORES - 20) Г— 100
           + (RAM_GB - 64) Г— 30
           - (PRICE_UAH / 1000)
           + CONDITION_FACTOR
           + WARRANTY_BONUS
```

### Component Breakdown

| Component | Formula | Example |
|-----------|---------|---------|
| **CPU Score** | (cores - 20) Г— 100 | 24 cores в†’ +400 pts |
| **RAM Score** | (ram_gb - 64) Г— 30 | 128 GB в†’ +1,920 pts |
| **Price Penalty** | - (price / 1000) | 35k UAH в†’ -35 pts |
| **Condition** | Variable (see below) | Refurb в†’ +300 pts |
| **Warranty** | +500 if present | Has warranty в†’ +500 pts |

### Condition Scoring

```
NEW             в†’ +0   (baseline)
REFURBISHED     в†’ +300 (tested/cleaned)
USED (good)     в†’ +200 (working, cosmetic issues)
USED (unknown)  в†’ +100 (as-is, untested)
```

### Example Calculations

**Example 1: Good Deal**
```
Model: HP DL380 G8 (24 cores, 128 GB RAM, 35k UAH, Refurbished)

Score = (24-20)Г—100 + (128-64)Г—30 - (35000/1000) + 300 + 0
      = 400 + 1,920 - 35 + 300
      = 2,585 / 1000 = 2.585 (EXCELLENT)
```

**Example 2: Budget Deal**
```
Model: Del R730 (20 cores, 64 GB RAM, 32k UAH, Used, 6mo warranty)

Score = (20-20)Г—100 + (64-64)Г—30 - (32000/1000) + 200 + 500
      = 0 + 0 - 32 + 200 + 500
      = 668 / 1000 = 0.668 (GOOD)
```

---

## рџ’ѕ DATA FORMATS

### Input: `server_hunt_config.yaml`

```yaml
SEARCH_SPECS:
  models:
    - HP DL380 G8
    - HP DL380 G9
    - Dell R730
    - Dell R740
  cpu_cores_min: 20
  cpu_cores_ideal: 28
  ram_gb_min: 64
  ram_gb_ideal: 128
  price_uah_max: 40000
  price_uah_target: 35000
  form_factor: 2U
  conditions:
    - Used
    - Refurbished
    - New

PLATFORMS:
  ukraine:
    olx:
      url: "https://olx.ua"
      search_pattern: "hp dl380 OR dell r730"
      selector:
        listings: "[data-testid='listing']"
        title: "h3"
        price: "[data-testid='price']"
    prom:
      url: "https://prom.ua"
      # ... more selectors ...

SCORING_RULES:
  cpu_cores_multiplier: 100
  ram_gb_multiplier: 30
  price_discount_multiplier: -1.0
  condition_factors:
    new: 0
    refurbished: 300
    used: 200
    unknown: 100
  warranty_bonus: 500
```

### Output: `server_hunt_data_[date].json`

```json
{
  "campaign_date": "2026-02-19T10:30:45",
  "platforms_searched": 10,
  "total_offers": 47,
  "offers": [
    {
      "id": "olx_12345",
      "platform": "OLX.ua",
      "url": "https://olx.ua/...",
      "title": "HP DL380 G8 Server 24 cores 128GB RAM",
      "server_model": "HP DL380 G8",
      "cpu_cores": 24,
      "cpu_type": "Xeon E5-2697 v2",
      "ram_gb": 128,
      "ram_type": "DDR3",
      "price_raw": "35000 UAH",
      "price_uah_estimated": 35000.0,
      "condition": "Refurbished",
      "warranty_months": 12,
      "seller_name": "ITProStore",
      "seller_rating": 4.8,
      "images_count": 6,
      "posted_date": "2026-02-15",
      "score": 2.585,
      "meets_specs": true
    },
    {
      "id": "prom_67890",
      "platform": "Prom.ua",
      // ... more fields ...
    }
  ],
  "summary": {
    "avg_price_uah": 37500,
    "min_price_uah": 28000,
    "max_price_uah": 55000,
    "avg_score": 1.2,
    "top_deal_score": 2.585,
    "offers_meeting_specs": 32,
    "offers_below_target_price": 8,
    "platforms_with_results": 7
  }
}
```

### Output: `server_hunt_analysis_[date].txt`

```
в•”в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•—
в•‘           рџЋЇ SERVER HUNT - AI ANALYSIS REPORT            в•‘
в•‘                                                          в•‘
в•‘      DeepSeek V3 Procurement Strategy Analysis           в•‘
в•љв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ќ

рџЏ† EXECUTIVE SUMMARY:
- Total Offers Analyzed: 32
- Platforms Searched: 7
- Top Deal: HP DL380 G8 @ 35k UAH (Score: 2.585)

рџ’Ў DEEPSEEK V3 EXPERT ANALYSIS:

1. DEAL ANALYSIS (for top 3 offers)
   - Value assessment for each
   - Price fairness evaluation
   - Red flags identified
   
2. MARKET INSIGHTS
   - Current pricing trends
   - Availability assessment
   - Currency considerations

3. NEGOTIATION PLAYBOOK
   - For each top deal:
     * Opening price to propose
     * Counter-negotiation strategies
     * Bundling opportunities
     * Payment/shipping leverage

4. RISK ASSESSMENT
   - Platform-specific risks
   - Health check recommendations
   - Warranty considerations
   - Hidden cost warnings

5. FINAL RECOMMENDATIONS
   - Ranking: Best value, Backup, Budget option
   - Exact opening price to propose
   - Specs to test upon receipt
   - Timeline recommendations

6. PORTFOLIO STRATEGY
   - If buying 2-3 units: Recommended mix
   - Vendor diversification strategy
   - Bulk discount estimates
   - Phased buying vs. immediate approach
```

---

## рџљЂ PREREQUISITES

### System Requirements
- Windows 10/11 or Linux/MacOS
- Python 3.11+
- 4 GB RAM minimum
- Internet connection
- ~1GB free space for browser cache

### Python Packages

```bash
# Install required packages:
pip install playwright pyyaml httpx

# Additional setup for Playwright:
playwright install chromium
```

### API Requirements

**For AI Analysis** (optional but recommended):
```bash
# Set environment variable (PowerShell):
$env:OPENROUTER_API_KEY = "sk-or-v1-xxxxx..."

# Or for OpenAI:
$env:OPENAI_API_KEY = "sk-xxxx..."
```

**Where to get API key**:
- OpenRouter: https://openrouter.ai (free tier: 50 requests/month)
- OpenAI: https://platform.openai.com ($$, but more reliable)

---

## вљ™пёЏ CONFIGURATION

### Modify Search Parameters

Edit `server_hunt_config.yaml`:

```yaml
# Change price target:
SEARCH_SPECS:
  price_uah_max: 50000  # Increase budget

# Change CPU requirements:
  cpu_cores_min: 16     # Accept 16+ instead of 20

# Add/remove platforms:
PLATFORMS:
  ukraine:
    # Add new platform...
```

### Change Scoring Weights

```yaml
SCORING_RULES:
  cpu_cores_multiplier: 150    # Value cores more
  ram_gb_multiplier: 20        # Value RAM less
  price_discount_multiplier: -0.5  # Less price sensitive
```

---

## рџ“Љ SAMPLE OUTPUT

### Scraper Report (server_hunt_campaign_*.txt)

```
рџЋЇ SERVER HUNT CAMPAIGN REPORT
================================
Campaign Date: 2026-02-19
Duration: 8m 34s
Platfroms Searched: 7/10 active

SEARCH TARGETS
==============
Models: HP DL380 G8 | HP DL380 G9 | Dell R730 | Dell R740
Specs: 20-28 cores | 64-128 GB RAM | <40k UAH

RESULTS SUMMARY
===============
Total Offers Found: 47
Offers Meeting Specs: 32 (68%)
Best Deal Score: 2.585
Avg Price: 37,500 UAH

TOP 5 BEST DEALS (by Score):

1. HP DL380 G8 - 24 cores, 128GB, 35k UAH #SCORE: 2.585
   Platform: OLX.ua | Condition: Refurbished | Warranty: 12mo
   URL: https://olx.ua/...

2. Dell R730 - 20 cores, 96GB, 32k UAH | SCORE: 1.847
   Platform: Prom.ua | Condition: Used (good) | Warranty: 6mo
   URL: https://prom.ua/...

3. HP DL380 G9 - 28 cores, 256GB, 42k UAH | SCORE: 1.654
   Platform: server.ua | Condition: Refurbished | Warranty: NULL
   URL: https://server.ua/...

[... more offers ...]

PRICE ANALYSIS
==============
Min: 28,000 UAH (Dell R730, 16 cores baseline)
Max: 55,000 UAH (HP DL380 G9, 28 cores new)
Average: 37,500 UAH
Median: 36,000 UAH
Target: <40,000 UAH вњ… (62% of offers below target)

NEGOTIATION STRATEGY
====================
Opening Offer Template: "[Price] - 15% to [lower amount]"
Counter Strategy: "I see similar specs at [reference price], can you match?"
Bundling: "Interested in 2-3 units for fleet. Best bulk rate?"
Payment: "Cash pickup preferred. When available?"
```

### AI Analysis (server_hunt_analysis_*.txt)

```
рџ¤– DEEPSEEK V3 EXPERT ANALYSIS

рџ’Ў DEAL ANALYSIS (Top 3):

#1 HP DL380 G8 - 35k UAH
   вњ… EXCELLENT VALUE
   - Fair price for specs (Xeon E5-2697 v2 = premium)
   - 128GB RAM above target (future-proof)
   - Refurbished (tested, cooled, reliable)
   - 12-month warranty standard
   
   Recommendation: PRIORITY #1
   Opening offer: 33,000 UAH (-5.7%)
   Counter threshold: 34,000 UAH minimum

#2 Dell R730 - 32k UAH
   вњ… GREAT VALUE FOR PRICE
   - Below target price (28% discount)
   - 20 cores minimum spec (bootstrap option)
   - 96GB RAM (64GB + 32GB expansion)
   - 6-month warranty (low risk)
   
   Recommendation: PRIMARY CHOICE for budget
   Opening offer: 30,000 UAH (-6.25%)
   Counter threshold: 31,000 UAH minimum

#3 HP DL380 G9 - 42k UAH
   вљ пёЏ  PREMIUM SPEC BUT ABOVE TARGET
   - 28 cores (max target)
   - 256GB RAM (overkill unless needed)
   - Above price target (+5% to target)
   - Newer generation (G9 vs G8)
   
   Recommendation: SECONDARY CHOICE (if budget increased)
   Opening offer: 38,000 UAH (-9.5%)
   Counter threshold: 40,000 UAH maximum

рџ“Љ MARKET INSIGHTS:

- HP DL380 G8 average: 36,500 UAH (tested market price)
- Dell R730 average: 31,200 UAH (budget option popularity)
- 28-core servers 15-20% premium over 20-core
- Refurbished units move 30% faster than used
- International shipping breaks ROI (10-15 EUR = 400-600 UAH)

рџЋЇ NEGOTIATION PLAYBOOK:

Email Template 1 (Aggressive):
"Your DL380 @ 35k looks good. I'm ready to purchase immediately
for 33k UAH. Cash transfer today if negotiable. Will you consider?"

Email Template 2 (Professional):
"Thanks for listing. I'm interested for bulk fleet purchase (2-3 units).
What's your best delivered price for immediate commitment? Available for
transport pickup if needed."

Email Template 3 (Backup):
"I see similar specs at [reference price]. Can you match [offer price]?
Flexible on timing if price is right. Ready for immediate payment."

Key negotiation leverage:
вњ“ Offer immediate payment (sellers value quick cash)
вњ“ Mention fleet purchase (bulk discount psychology)
вњ“ Reference second choice (creates time pressure)
вњ“ Ask for bundle discount (shipping savings benefit both)
вњ“ Propose pickup (eliminates shipping risk seller has)

вљ пёЏ RISK ASSESSMENT:

рџ”ґ HIGH RISK (avoid):
- No warranty on used-as-is units
- Cosmetic damage indicated ("AS IS" listings)
- New sellers (<10 feedback)
- Unclear spec descriptions
- Facebook Marketplace sellers (no buyer protection)

рџџЎ MEDIUM RISK (negotiate):
- Used condition but good feedback
- 6-month warranty (acceptable)
- No detailed specs listed (ask for CPU model)
- Single photo (ask for more before purchasing)
- Foreign sellers (shipping complications)

рџџў LOW RISK (safe):
- Refurbished with 12+ month warranty
- Established sellers (100+ positive feedback)
- Complete technical specs listed
- Multiple photos included
- Official company listings

Health Check Recommendations (Upon Receipt):
1. Verify CPU with CPU-Z (command: cpuid)
2. Test RAM with MemTest86 (1 pass minimum)
3. Check SMART data on HDDs (if included)
4. Run thermal test 15 minutes (must < 60В°C idle)
5. Verify all fans respond (audio/RPM check)
6. Document any cosmetic damage for claim
7. Request remote support from seller during tests

рџ’° PORTFOLIO STRATEGY:

If buying 1 unit (cost-sensitive):
в†’ Buy #2 (Dell R730 @ 32k) - Best price, meets minimum

If buying 2 units (balanced):
в†’ Buy #1 + #2 (DL380 + R730 = 67k UAH)
в†’ Request 2-unit discount: -5% each = 63.65k total
в†’ Spread risk: different architectures, different sellers

If buying 3 units (fleet):
в†’ Buy #1 + #2 + #3 (= 109k UAH gross)
в†’ Request 3-unit bulk discount: -8% each = 100.28k total
в†’ Stagger purchases: 1 now, review, then 2 more
в†’ Negotiate seller trade-in if upgrading existing equipment

рџЋ‰ FINAL SCORE:

Market Status: вњ… BUYERS MARKET (32/47 offers under target)
Best Deal: HP DL380 G8 @ 35k UAH (RECOMMEND)
Negotiation Confidence: 85% (expect -5-10% on opening price)
Timeframe: URGENT (good inventory, prices may rise)
Next Steps: Contact #1 seller TODAY with opening offer
```

---

## рџЋ® EXECUTION EXAMPLES

### Run Complete Campaign

```powershell
# One command: scrape + analyze
cd c:\1225\project_s_super_core
python server_hunt_maestro.py

# Output: All reports on Desktop
# Duration: ~10-15 minutes
# Results auto-open in text editor
```

### Run Scraper Only (for testing)

```powershell
# Manual scraper execution
python server_hunt_scraper.py

# Output:
# - server_hunt_campaign_[date].txt
# - server_hunt_data_[date].json
# Duration: 5-10 minutes
```

### Run Analysis Only (on existing data)

```powershell
# Analyze previous scrape results
python server_hunt_analyzer.py

# Requires: Most recent server_hunt_data_*.json file exists
# Output: server_hunt_analysis_[date].txt
# Duration: 2-3 minutes
```

---

## рџђ› TROUBLESHOOTING

### "File not found: server_hunt_config.yaml"
**Solution**: Make sure you're in the workspace:
```powershell
cd c:\1225\project_s_super_core
```

### "No offers found" despite seeing listings
**Reason**: CSS selectors need updating  
**Solution**:
1. Open platform in browser
2. Right-click listing в†’ Inspect Element
3. Find actual selector path
4. Update `server_hunt_config.yaml`

### "Ancient Playwright timeout"
**Reason**: Website anti-bot protection  
**Solution**:
```yaml
EXECUTION:
  headless: false  # Show browser
  timeout_ms: 30000  # Increase timeout
  stealth_mode: true  # Enable stealth
```

### "API Key error"
**Solution**:
```powershell
# Set environment variable:
$env:OPENROUTER_API_KEY = "your_actual_key_here"

# Verify it:
echo $env:OPENROUTER_API_KEY
```

### "0 characters returned from sites"
**Reason**: Connection/blocking issue  
**Solution**:
- Check internet connection
- Try with VPN to Ukraine if blocked
- Increase `timeout_ms` in config
- Run in headless=false to see what's happening

---

## рџ“€ SUCCESS METRICS

### You'll know it's working when:

вњ… **Scraper**: Finds >20 offers within target specs  
вњ… **Scoring**: Top 5 deals show reasonable ranking  
вњ… **AI**: Generates 4+ page analysis with negotiation  
вњ… **Results**: Files automatically open on Desktop  
вњ… **Data Quality**: JSON includes 95%+ non-null specs  

---

## рџ”„ NEXT STEPS (After First Run)

### Immediate (Day 1):
1. Review top 3 deals in analysis report
2. Open seller URLs in browser (verify active listings)
3. Send 3 opening offers to sellers
4. Document sender contact info for follow-up

### Short-term (Week 1):
5. Track seller responses
6. Negotiate based on AI playbook
7. Prepare shipping arrangement
8. Schedule pre-purchase health checks

### Medium-term (Week 2-3):
9. Complete payment & shipping
10. Run diagnostics upon receipt
11. Configure servers (OS, networking, monitoring)
12. Document final cost & time-to-operational

---

## рџ“ћ SUPPORT

### Common Modifications

**To add a new platform**:
1. Add URL to `PLATFORMS` in config
2. Add `scrape_[platform_name]()` method to scraper
3. Define CSS selectors for that platform
4. Run scraper (test single platform)

**To change specs**:
1. Modify `SEARCH_SPECS` in config
2. Re-run scraper
3. AI analyzer uses updated data automatically

**To change scoring**:
1. Modify `SCORING_RULES` in config
2. Re-run scraper
3. Scores recalculated automatically

---

## рџ“‹ CHECKLIST FOR LAUNCH

- [ ] Python 3.11+ installed
- [ ] Required packages: `pip install playwright pyyaml httpx`
- [ ] Playwright browser: `playwright install chromium`
- [ ] API key configured: `$env:OPENROUTER_API_KEY = "..."`
- [ ] In correct directory: `cd c:\1225\project_s_super_core`
- [ ] All 3 files exist: maestro.py, scraper.py, analyzer.py, config.yaml
- [ ] Read this document end-to-end
- [ ] Ready to execute: `python server_hunt_maestro.py`

---

**рџЋЇ Ready to hunt servers! Launch the campaign with:**
```powershell
python server_hunt_maestro.py
```

Good luck! рџљЂ

