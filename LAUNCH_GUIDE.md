# рџљЂ SERVER HUNT LAUNCH GUIDE
## Complete Setup & Execution Instructions

**Status**: вњ… All components ready  
**Last Updated**: 2026-02-19  
**Version**: 1.0

---

## рџ“¦ WHAT YOU HAVE

Four production-ready Python scripts for complete server hunting campaign:

| File | Purpose | Size | Status |
|------|---------|------|--------|
| `server_hunt_maestro.py` | Orchestrator (Main Entry Point) | 12 KB | вњ… Ready |
| `server_hunt_scraper.py` | Web Scraping Engine | 14.5 KB | вњ… Ready |
| `server_hunt_analyzer.py` | AI Analysis Module | 11.8 KB | вњ… Ready |
| `server_hunt_config.yaml` | Configuration File | 2.5 KB | вњ… Ready |

Plus comprehensive documentation:
- `SERVER_HUNT_README.md` - Complete system documentation
- `LAUNCH_GUIDE.md` - This file

---

## вљЎ QUICK START (2 Minutes)

### Step 1: Install Dependencies

**Open PowerShell** and run:

```powershell
# Navigate to project
cd c:\1225\project_s_super_core

# Install Python packages
pip install playwright pyyaml httpx

# Setup Playwright browsers
playwright install chromium

# Verify installation
python -c "import playwright; print('вњ… OK')"
```

**Expected output**: `вњ… OK`

### Step 2: Configure API Key (Optional but Recommended)

For AI analysis, set your API key:

```powershell
# Using OpenRouter (recommended for free tier):
$env:OPENROUTER_API_KEY = "sk-or-v1-YOUR_KEY_HERE"

# Or using OpenAI (more expensive):
$env:OPENAI_API_KEY = "sk-YOUR_KEY_HERE"

# Verify it's set:
echo $env:OPENROUTER_API_KEY
```

**How to get API key**:
- **OpenRouter** (FREE): https://openrouter.ai в†’ Sign up в†’ API Keys
- **OpenAI** (PAID): https://platform.openai.com в†’ API Keys

### Step 3: Launch Campaign

```powershell
# Still in: c:\1225\project_s_super_core

# Run the complete campaign:
python server_hunt_maestro.py

# Or run scraper only (faster, no AI):
# python server_hunt_scraper.py

# Or analyze existing data:
# python server_hunt_analyzer.py
```

### Step 4: Review Results

Results auto-open on Desktop:
- `server_hunt_campaign_[timestamp].txt` - Scraping report with top deals
- `server_hunt_data_[timestamp].json` - Raw structured data
- `server_hunt_analysis_[timestamp].txt` - AI procurement recommendations

---

## рџ“‹ DETAILED SETUP

### Prerequisites Check

```powershell
# Python version
python --version
# Expected: Python 3.11 or higher

# Check pip
pip --version
# Expected: pip 20.0+

# Check internet
Test-NetConnection google.com -Port 443
# Expected: (no errors)
```

### Install Process (Step-by-Step)

#### 1. Python Packages

```powershell
# Core packages for web scraping
pip install playwright

# YAML configuration
pip install pyyaml

# HTTP client for API calls
pip install httpx

# Async utilities (included in Python 3.11+)
# No separate install needed
```

#### 2. Playwright Browser

```powershell
# Install Chromium browser
playwright install chromium

# Verify installation
playwright install --with-deps

# Test it works
python -c "from playwright.sync_api import sync_playwright; print('вњ… Playwright OK')"
```

#### 3. Verify All Components

```powershell
cd c:\1225\project_s_super_core

# Check files exist
ls server_hunt_*.py
ls server_hunt_config.yaml
ls SERVER_HUNT_README.md

# Expected: All 4 Python files + config + README

# Check syntax
python -m py_compile server_hunt_maestro.py
python -m py_compile server_hunt_scraper.py
python -m py_compile server_hunt_analyzer.py

# Expected: No errors
```

---

## рџЋЇ EXECUTION MODES

### Mode 1: Full Campaign (Recommended)

```powershell
python server_hunt_maestro.py
```

**What it does**:
1. вњ… Validates all files and dependencies
2. рџЊђ Scrapes 10 platforms (5-10 minutes)
3. рџ¤– Analyzes with DeepSeek AI (2-3 minutes)
4. рџ“Љ Generates comprehensive reports
5. рџ’ѕ Saves to Desktop
6. рџ–ҐпёЏ Opens results automatically

**Total duration**: ~15 minutes  
**Output files**: 3 (campaign report, JSON data, AI analysis)  
**Best for**: Initial discovery, complete analysis

### Mode 2: Scraping Only (Faster)

```powershell
python server_hunt_scraper.py
```

**What it does**:
1. рџЊђ Scrapes enabled platforms from config
2. рџ“Љ Generates scraper report
3. рџ’ѕ Saves structured JSON data
4. рџ–ҐпёЏ Opens report on Desktop

**Total duration**: 5-10 minutes  
**Output files**: 2 (campaign report, JSON data)  
**Best for**: Quick market check, testing, offline analysis

### Mode 3: Analysis Only (Requires Previous Data)

```powershell
python server_hunt_analyzer.py
```

**What it does**:
1. рџ“‚ Finds most recent server_hunt_data_*.json file
2. рџ“¤ Sends to DeepSeek V3 for analysis
3. рџ’Ў Generates AI recommendations
4. рџ’ѕ Saves analysis report
5. рџ–ҐпёЏ Opens on Desktop

**Total duration**: 2-3 minutes  
**Output files**: 1 (AI analysis)  
**Best for**: Analyzing previous scrapes, offline usage

---

## вљ™пёЏ CONFIGURATION

### Quick Config Changes

Edit `server_hunt_config.yaml`:

#### Increase budget:
```yaml
SEARCH_SPECS:
  price_uah_max: 50000  # Was 40000
```

#### Accept lower core count:
```yaml
SEARCH_SPECS:
  cpu_cores_min: 16  # Was 20
```

#### Focus on specific platforms:
```yaml
PLATFORMS:
  ukraine:
    olx:
      enabled: true
    prom:
      enabled: false  # Skip this one
```

#### Change deal scoring weight:
```yaml
SCORING_RULES:
  cpu_cores_multiplier: 150    # Favor CPU
  ram_gb_multiplier: 20         # Less RAM importance
  price_discount_multiplier: -0.5  # Less price-sensitive
```

**After editing config**: Simply re-run scraper (config auto-reloaded)

---

## рџ”§ TROUBLESHOOTING

### Problem: "No module named 'playwright'"

**Solution**:
```powershell
# Install missing package
pip install playwright

# Setup browsers
playwright install chromium

# Test
python -c "import playwright; print('OK')"
```

### Problem: "Playwright timeout"

**Reason**: Website loading slowly or anti-bot protection  
**Solution**:  
Edit `server_hunt_config.yaml`:
```yaml
EXECUTION:
  timeout_ms: 45000  # Increase from 30000
  headless: false    # Show browser to debug
```

### Problem: "No OPENROUTER_API_KEY set"

**Reason**: Missing API key environment variable  
**Solution**:
```powershell
# Set key
$env:OPENROUTER_API_KEY = "sk-or-v1-YOUR_KEY_HERE"

# Verify
echo $env:OPENROUTER_API_KEY

# Get key from https://openrouter.ai
```

### Problem: "0 characters from site"

**Reason**: CSS selectors don't match site  
**Solution**:
1. Open site in browser
2. Right-click listing в†’ Inspect Element
3. Find actual selector
4. Update `server_hunt_config.yaml` PLATFORMS section

### Problem: "FileNotFoundError: server_hunt_config.yaml"

**Solution**:
```powershell
# Make sure you're in correct directory
cd c:\1225\project_s_super_core

# Verify file exists
ls server_hunt_config.yaml

# Then run
python server_hunt_maestro.py
```

### Problem: "Connection refused" or network error

**Solutions**:
1. Check internet connection
```powershell
Test-NetConnection -ComputerName openrouter.ai -Port 443
```

2. Try with VPN to Ukraine (if blocked)

3. Increase timeout in config:
```yaml
EXECUTION:
  timeout_ms: 60000
  retry_attempts: 3
```

---

## рџ“Љ MONITORING EXECUTION

### While Running

You'll see console output like:

```
[10:30:45] рџЋЇ SERVER HUNT MAESTRO v1.0
[10:30:45] вњ… Validating required files...
[10:30:46] рџЊђ Starting browser automation...
[10:30:47]    Scraping OLX.ua...
[10:31:15]    Scraping Prom.ua...
[10:31:45] вњ… Scraping complete (78 offers found)
...
[10:33:20] вњ… Data generation complete
[10:33:21] рџ¤– Launching DeepSeek V3 analyzer...
[10:35:45] вњ… AI analysis complete
[10:35:50] рџ“Ѓ Files saved to Desktop
```

### After Completion

Check Desktop for three files:
```
server_hunt_campaign_20260219_103050.txt
server_hunt_data_20260219_103050.json
server_hunt_analysis_20260219_103505.txt
```

---

## рџ“€ EXPECTED RESULTS

### Minimum Success Criteria

вњ… **Scraper** finds 20+ offers within 60 minutes  
вњ… **Scoring** produces reasonable deal rankings  
вњ… **AI** generates 3+ page analysis  
вњ… **Files** auto-open on Desktop  
вњ… **Data** is >95% complete (non-null specs)

### Example Results

```
Total Offers Found: 47
Offers Meeting Specs: 32 (68%)
Best Deal: HP DL380 G8 @ 35,000 UAH
Average Price: 37,500 UAH
Score Range: 0.5 - 2.8

Top 3 Deals Identified вњ…
AI Negotiation Strategy вњ…
Portfolio Recommendations вњ…
Risk Assessment вњ…
```

---

## рџЋЇ NEXT ACTIONS (After First Run)

### Immediate (1-2 hours):

1. **Review Results**
   - Open `server_hunt_analysis_*.txt`
   - Read "FINAL RECOMMENDATIONS" section
   - Identify top 3 deals

2. **Verify Sellers**
   - Open each URL in browser
   - Check if still listed (active)
   - Note seller rating/feedback
   - Look for contact info

3. **Prepare Offers**
   - Use AI-recommended opening price
   - Draft negotiation email
   - Collect USD pricing (reference)

### Short-term (Day 1):

4. **Contact Sellers**
   - Send opening offers to top 3
   - Ask for technical specs
   - Inquire about bulk discount
   - Request more photos

5. **Negotiate**
   - Use AI playbook for counter-offers
   - Leverage bulk purchase angle
   - Offer immediate payment
   - Arrange logistics

---

## рџ’Ў TIPS & TRICKS

### Maximize Results

- **Run multiple times**: Different days get different listings
- **Modify specs**: Lower budget threshold finds more deals
- **Add platforms**: Uncomment disabled platforms in config
- **Adjust scoring**: Prioritize what matters most (CPU vs price)

### Save Time

- Skip AI analysis first, review scraper results
- Use scraper-only mode to test config changes
- Run analysis on multiple scrapes (find best data)

### Handle Anti-Bot

If sites block you:
1. Increase `timeout_ms` in config
2. Run with `headless: false` to see what's happening
3. Use VPN to Ukraine
4. Stagger runs (don't run multiple times per hour)

---

## рџ“ћ SUPPORT RESOURCES

### When Something Goes Wrong

1. **Check Python version**: `python --version` (need 3.11+)
2. **Verify packages**: `pip list | grep playwright`
3. **Test components**:
   ```powershell
   python -c "import playwright; import httpx; import yaml; print('OK')"
   ```
4. **Check config syntax**: `python -m yaml server_hunt_config.yaml`
5. **Review log output**: Copy-paste into chat for analysis

### Common Issues & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` | Package not installed | `pip install [package]` |
| `Timeout` | Website slow | Increase `timeout_ms` |
| `0 chars extracted` | Selector wrong | Update PLATFORMS in config |
| `No API key` | Environment variable missing | Set `$env:OPENROUTER_API_KEY` |
| `FileNotFoundError` | Wrong directory | `cd c:\1225\project_s_super_core` |
| `Connection refused` | Network/firewall | Check internet, try VPN |

---

## рџ“‹ FINAL CHECKLIST

Before launching for real:

- [ ] Python 3.11+ installed (`python --version`)
- [ ] Packages installed (`pip install playwright pyyaml httpx`)
- [ ] Playwright setup (`playwright install chromium`)
- [ ] Correct directory (`cd c:\1225\project_s_super_core`)
- [ ] All files present (`ls server_hunt_*.py server_hunt_config.yaml`)
- [ ] Config reviewed (optional: `server_hunt_config.yaml`)
- [ ] API key set (optional: `$env:OPENROUTER_API_KEY = "..."`)
- [ ] No internet issues (can reach openrouter.ai, olx.ua, etc.)

---

## рџљЂ LAUNCH!

Once you've completed the checklist above:

```powershell
cd c:\1225\project_s_super_core

# Run the campaign:
python server_hunt_maestro.py

# Sit back and wait for results (15 minutes)
# Results will open on Desktop automatically
```

**Good luck with your server hunting! рџЋЇ**

Questions? Check `SERVER_HUNT_README.md` for complete documentation.

