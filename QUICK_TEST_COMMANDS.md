# VALÓS FELADATOK - GYORS TESZT PARANCSOK

## 1. Gyakorlati Feladatok (100% Garantált)

```bash
# 6 feladat, 10+ fájl, < 1 mp
python test_practical_tasks.py
```

**Kie**: Database-k, Cloud Platforms, Web Frameworks, Tools Overview  
**Output**: 10 JSON + CSV fájl  
**Státusz**: Garantáltan működik

---

## 2. AI Feldolgozás + Gyakorlati (Vegyes Teszt)

```bash
# 6 feladat: 3 AI + 3 gyakorlati
# 12+ fájl, ~2 perc
python test_mixed_ai_practical.py
```

**AI Feladatok**: GitHub analízis, Tech trendek, Developer report  
**Gyakorlati**: Database-k, Cloud, Frameworks  
**Output**: 12 JSON + CSV, 1 PDF  
**Státusz**: Teljes teszt

---

## 3. Közvetlen Feladat Adás

```bash
# Közvetlenül az AI-nak
python feladat.py "Szamold ossze az 16 tool funkciot es nevet"
```

**Output**: Console output + memory/output/ fájlok  
**Feldolgozás**: ~30 mp  
**Státusz**: Real-time AI response

---

## 4. Interaktív Teszt

```bash
# Menü alapú feladat választás
python task.py
```

**Lehetőségek**:
1. Előre definiált feladatok
2. Egyedi feladat input  
3. Valós API tesztek

**Státusz**: Interactive mode

---

## 5. Statusz Ellenőrzés

```bash
# Teljes projekt inicializálás
python startup.py
```

**Ellenőrzések**: Struktúra, launcher, tesztek  
**Output**: Comprehensive status report  
**Státusz**: Health check

---

## 6. Eredmények Megtekintése

```bash
# Tesztelés eredménye summary
python show_test_results.py
```

**Output**: 
- Kimeneti fájlok listája
- AI feldolgozások
- Tool statisztika
- Summary JSON

---

## 7. Fájlok Ellenőrzése

```bash
# Memory/output mappa tartalmát
Get-ChildItem memory\output -Name | Sort

# Legutóbbi fájlok
Get-ChildItem memory\output | Sort-Object LastWriteTime -Descending | Select -First 10
```

---

## Gyors Teszt Sorrend

### Teljes Megoldás (5 perc)

```bash
# 1. Gyakorlati feladatok
python test_practical_tasks.py

# 2. AI + Gyakorlati vegyes teszt
python test_mixed_ai_practical.py

# 3. Eredmények megtekintése
python show_test_results.py

# 4. Fájlok ellenőrzése
python show_test_results.py
```

### Csak AI Teszt (2 perc)

```bash
# Vegyes teszt (3 AI + 3 gyakorlati)
python test_mixed_ai_practical.py 2>&1 | Select-Object -Last 40
```

### Gyors Proof-of-Concept (30 sec)

```bash
# Gyakorlati feladatok
python test_practical_tasks.py 2>&1 | Select-Object -Last 15
```

---

## Output Fájlok Helye

```
memory/output/
├── github_top_repos.json      (AI GitHub)
├── tech_categories.json       (AI Trends)
├── databases.json             (Praktikai)
├── databases.csv
├── cloud_platforms.json       (Praktikai)
├── cloud_platforms.csv
├── frameworks.json            (Praktikai)
├── frameworks.csv
├── available_tools.json       (Praktikai)
├── available_tools.csv
├── public_apis.json           (Praktikai)
├── public_apis.csv
└── test_summary.json          (Összefoglaló)
```

---

## Tool-ok Referencia

### 16 Elérhet ő Tool

| # | Tool | Kategória | Teszt |
|---|------|-----------|-------|
| 1 | file_reader | File I/O | ✓ |
| 2 | file_writer | File I/O | ✓ |
| 3 | file_search | File I/O | - |
| 4 | web_api_call | Web | ✓ |
| 5 | web_scraper | Web | ✓ |
| 6 | web_analyzer | Web | - |
| 7 | web_page_fetch | Web | - |
| 8 | web_search | Web | - |
| 9 | pdf_generator | Gen. | ✓ |
| 10 | system_command | System | - |
| 11 | system_info | System | - |
| 12 | general_assistant | AI | ✓ |
| 13 | tech_news_aggregator | Web | ✓ |
| 14 | browser_automation | Browser | - |
| 15 | optimized_browser_automation | Browser | - |
| 16 | ultra_optimized_browser_automation | Browser | - |

---

## Debuggolás

### Ha egy feladat nem működik

```bash
# 1. Ellenőrizd a registry
python -c "from tools.tools.registry.tool_registry_golden import ToolRegistry; r = ToolRegistry(); print(f'{len(r.tools)} tools')"

# 2. Ellenőrizd a fájlokat
Get-ChildItem memory/output | Measure-Object -Property Length -Sum

# 3. Startup teszt
python super_intelligent_launcher.py --smoke
```

---

## Teljesítményadatok

| Teszt | Idő | Fájlok | Státusz |
|-------|-----|--------|---------|
| Praktikai | < 1 sec | 10 | ✅ |
| Vegyes | ~2 min | 12+ | ✅ |
| AI Feladat | ~30 sec | 1+ | ✅ |
| Startup | ~5 sec | - | ✅ |

---

## Dokumentáció

```
PROJECT_STATUS.md      - Teljes projekt státusz
README.md              - Felhasználói útmutató
TEST_RESULTS_SUMMARY.md - Teszt eredmények
COPILOT_RULES.md       - Architecture guidelines
```

---

**Verzió**: Project-S v0.1-stable  
**Utolsó Update**: 2025-12-26  
**Státusz**: ✅ FULLY OPERATIONAL
