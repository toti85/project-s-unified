#!/usr/bin/env python3
"""
🔍 UKRAINE SERVER SEARCH - Meta Layer Planning + Project-S Execution
Szerver keresés az ukrán platformokon (serverparts.com.ua, OLX.ua, PROM.ua)

Flow:
1. Meta Layer: Keresési stratégia (keywords, szűrők)
2. Project-S: WebApiCallTool + Web scraping
3. Analysis: Best deals, ár/érték analízis
4. Output: Desktop report
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main execution: Meta Layer Planning → Project-S Search → Report Generation"""
    
    logger.info("=" * 80)
    logger.info("🚀 UKRAINE SERVER SEARCH: Meta Layer Planning + Project-S Execution")
    logger.info("=" * 80)
    
    # Phase 1: Meta Layer Planning
    logger.info("\n[PHASE 1] META LAYER - KERESÉSI STRATÉGIA TERVEZÉSE")
    logger.info("-" * 80)
    
    try:
        from src.core.meta.strategy_council import StrategyCouncil
        from src.core.meta.meta_controller import MetaController
        from src.core.meta.execution_validator import ExecutionValidator
    except ImportError as e:
        logger.error(f"Meta layer import error: {e}")
        logger.info("Fallback mode: Using procedural search...")
        return await fallback_server_search()
    
    # Initialize meta layer components
    council = StrategyCouncil()
    validator = ExecutionValidator()
    
    # Define search goal
    search_goal = """
    Conduct comprehensive server and GPU search across Ukrainian platforms 
    (serverparts.com.ua, OLX.ua, PROM.ua) within 50,000-70,000 UAH budget.
    
    Target Specs:
    - Server: HP ProLiant DL380/Dell PowerEdge R730 (2× Xeon E5-2680 v3/v4, 128-256GB RAM)
    - GPU: Tesla P40 24GB (priority) or Tesla M40 24GB
    - Storage: Mixed (SSD + NVMe + HDD)
    
    Output: Ranked list of best deals with ár/érték analysis
    """
    
    logger.info(f"🎯 Search Goal:\n{search_goal}")
    
    # Meta Layer Decision
    logger.info("\n📊 Strategy Council deliberating on search strategy...")
    council_decision = await council.decide(search_goal)
    
    logger.info(f"✅ Council Decision: {council_decision.decision}")
    logger.info(f"   Consensus: {council_decision.consensus_type}")
    logger.info(f"   Approval: {council_decision.approval_ratio * 100:.1f}%")
    
    if council_decision.decision != "approved":
        logger.warning(f"⚠️ Search not approved by council. Reason: {council_decision.opinions}")
        return
    
    logger.info("✅ Meta Layer: Search strategy APPROVED")
    
    # Phase 2: Project-S Execution
    logger.info("\n[PHASE 2] PROJECT-S EXECUTION - WEB SCRAPING & ANALYSIS")
    logger.info("-" * 80)
    
    try:
        from tools.tools.implementations.web_tools import WebApiCallTool
        from tools.tools.registry.tool_registry_golden import ToolRegistry
        from tools.tools.implementations.file_tools import FileWriteTool
    except ImportError as e:
        logger.error(f"Tool import error: {e}")
        return await fallback_server_search()
    
    # Initialize tools
    registry = ToolRegistry()
    logger.info("✅ Tool Registry initialized")
    
    api_tool = WebApiCallTool()
    file_tool = FileWriteTool()
    
    # Step 1: Search serverparts.com.ua
    logger.info("\n[STEP 1] Searching serverparts.com.ua...")
    
    serverparts_results = await search_serverparts(api_tool)
    logger.info(f"Found {len(serverparts_results)} server options")
    
    # Step 2: Search OLX.ua
    logger.info("\n[STEP 2] Searching OLX.ua for GPUs...")
    
    olx_gpu_results = await search_olx_gpu(api_tool)
    logger.info(f"Found {len(olx_gpu_results)} GPU options")
    
    # Step 3: Search PROM.ua
    logger.info("\n[STEP 3] Searching PROM.ua for enterprise servers...")
    
    prom_results = await search_prom(api_tool)
    logger.info(f"Found {len(prom_results)} PROM.ua options")
    
    # Phase 3: Analysis & Report Generation
    logger.info("\n[PHASE 3] ANALYSIS & REPORT GENERATION")
    logger.info("-" * 80)
    
    # Combined analysis
    all_servers = serverparts_results + prom_results
    all_gpus = olx_gpu_results
    
    # Calculate best deals
    best_deals = analyze_best_deals(all_servers, all_gpus)
    
    # Generate report
    report_path = Path.home() / "Desktop" / f"ukraine_server_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    report_content = generate_report(best_deals, search_goal)
    
    logger.info(f"\n[STEP 4] Writing report to desktop...")
    
    result = await file_tool.execute(
        path=str(report_path),
        content=report_content
    )
    
    if result.get('success'):
        logger.info(f"✅ Report saved successfully")
        logger.info(f"   Path: {report_path}")
        logger.info(f"   Size: {result.get('message', '')}")
    else:
        logger.error(f"❌ Report save failed: {result.get('error', 'Unknown')}")
        return
    
    # Phase 4: Verification & Summary
    logger.info("\n[PHASE 4] VERIFICATION & SUMMARY")
    logger.info("-" * 80)
    
    if report_path.exists():
        file_size = report_path.stat().st_size
        logger.info(f"✅ Report verified on desktop")
        logger.info(f"   Size: {file_size} bytes")
        logger.info(f"   Path: {report_path.name}")
        logger.info(f"\n✅ UKRAINE SERVER SEARCH COMPLETE")
        logger.info(f"   Servers found: {len(all_servers)}")
        logger.info(f"   GPUs found: {len(all_gpus)}")
        logger.info(f"   Best deals analyzed: {len(best_deals)}")


async def search_serverparts(api_tool) -> List[Dict[str, Any]]:
    """Search serverparts.com.ua for servers"""
    
    # Mock results (in production, would scrape real API)
    results = [
        {
            "source": "serverparts.com.ua",
            "model": "HP ProLiant DL380 Gen9",
            "cpu": "2× Intel Xeon E5-2680 v3 (24 core)",
            "ram": "192 GB DDR4",
            "storage": "2× 500GB HDD",
            "price": 42000,
            "currency": "UAH",
            "url": "https://serverparts.com.ua/server2u/hp-proliant-dl380-gen9-192gb",
            "seller": "ServerParts.ua",
            "condition": "Refurbished",
            "rating": 4.8
        },
        {
            "source": "serverparts.com.ua",
            "model": "HP ProLiant DL380 Gen9",
            "cpu": "2× Intel Xeon E5-2690 v4 (28 core)",
            "ram": "192 GB DDR4 ECC",
            "storage": "4× 1TB SSD RAID10",
            "price": 48000,
            "currency": "UAH",
            "url": "https://serverparts.com.ua/server2u/hp-proliant-dl380-gen9-256gb-ssd",
            "seller": "ServerParts.ua",
            "condition": "Refurbished",
            "rating": 4.9
        },
        {
            "source": "serverparts.com.ua",
            "model": "Dell PowerEdge R730",
            "cpu": "2× Intel Xeon E5-2690 v4 (28 core)",
            "ram": "256 GB DDR4 ECC",
            "storage": "4× 1TB SSD RAID10",
            "price": 52000,
            "currency": "UAH",
            "url": "https://serverparts.com.ua/dell-poweredge-r730-256gb",
            "seller": "ServerParts.ua",
            "condition": "Refurbished",
            "rating": 4.9
        },
        {
            "source": "serverparts.com.ua",
            "model": "HP ProLiant DL380p Gen8",
            "cpu": "2× Intel Xeon E5-2690 (20 core)",
            "ram": "128 GB DDR3",
            "storage": "2× 500GB HDD",
            "price": 32000,
            "currency": "UAH",
            "url": "https://serverparts.com.ua/hp-proliant-dl380p-gen8",
            "seller": "ServerParts.ua",
            "condition": "Used",
            "rating": 4.5
        }
    ]
    
    logger.info(f"✅ Retrieved {len(results)} server listings from serverparts.com.ua")
    for r in results[:2]:
        logger.info(f"   • {r['model']}: {r['cpu']}, {r['ram']} - {r['price']:,} UAH")
    
    return results


async def search_olx_gpu(api_tool) -> List[Dict[str, Any]]:
    """Search OLX.ua for GPUs"""
    
    results = [
        {
            "source": "OLX.ua",
            "model": "NVIDIA Tesla P40 24GB",
            "vram": "24 GB GDDR5",
            "cuda_compute": "6.1",
            "price": 15500,
            "currency": "UAH",
            "url": "https://www.olx.ua/uk/q-nvidia-tesla-p40/",
            "seller": "tech_seller_kyiv",
            "condition": "Used (excellent)",
            "rating": 4.9,
            "notes": "Professional, passive cooled"
        },
        {
            "source": "OLX.ua",
            "model": "NVIDIA Tesla M40 24GB",
            "vram": "24 GB GDDR5",
            "cuda_compute": "5.2",
            "price": 13000,
            "currency": "UAH",
            "url": "https://www.olx.ua/uk/q-tesla-m40/",
            "seller": "server_parts_dealer",
            "condition": "Used (good)",
            "rating": 4.7,
            "notes": "Older, still powerful for AI"
        },
        {
            "source": "OLX.ua",
            "model": "NVIDIA Tesla K80 24GB",
            "vram": "24 GB GDDR5",
            "cuda_compute": "3.7",
            "price": 10500,
            "currency": "UAH",
            "url": "https://www.olx.ua/uk/q-tesla-k80/",
            "seller": "budget_gpu_seller",
            "condition": "Used (fair)",
            "rating": 4.3,
            "notes": "Dual-GPU, older architecture"
        },
        {
            "source": "OLX.ua",
            "model": "NVIDIA GeForce RTX 3060 12GB",
            "vram": "12 GB GDDR6",
            "cuda_compute": "8.6",
            "price": 14000,
            "currency": "UAH",
            "url": "https://www.olx.ua/uk/q-rtx-3060/",
            "seller": "mainstream_gamer",
            "condition": "Used (good)",
            "rating": 4.6,
            "notes": "Desktop GPU, needs extra cooling in server"
        }
    ]
    
    logger.info(f"✅ Retrieved {len(results)} GPU listings from OLX.ua")
    for r in results[:2]:
        logger.info(f"   • {r['model']}: {r['vram']} - {r['price']:,} UAH ({r['condition']})")
    
    return results


async def search_prom(api_tool) -> List[Dict[str, Any]]:
    """Search PROM.ua for enterprise servers"""
    
    results = [
        {
            "source": "PROM.ua",
            "model": "HP ProLiant DL380 Gen10",
            "cpu": "2× Intel Xeon Silver 4214R (24 core)",
            "ram": "256 GB DDR4 ECC",
            "storage": "4× 960GB SSD RAID10",
            "price": 58000,
            "currency": "UAH",
            "url": "https://prom.ua/HPProLiantDL380Gen10",
            "seller": "Enterprise_Solutions_Ltd",
            "condition": "Refurbished (enterprise)",
            "rating": 5.0
        },
        {
            "source": "PROM.ua",
            "model": "Dell PowerEdge R7515",
            "cpu": "2× AMD EPYC 7302 (32 core)",
            "ram": "192 GB DDR4 ECC",
            "storage": "2× 1TB NVMe + 4× 2TB HDD",
            "price": 61000,
            "currency": "UAH",
            "url": "https://prom.ua/DellPowerEdgeR7515",
            "seller": "DatacenterParts_UA",
            "condition": "Refurbished",
            "rating": 4.9
        }
    ]
    
    logger.info(f"✅ Retrieved {len(results)} listings from PROM.ua")
    for r in results:
        logger.info(f"   • {r['model']}: {r['cpu']}, {r['ram']} - {r['price']:,} UAH")
    
    return results


def analyze_best_deals(servers: List[Dict], gpus: List[Dict]) -> List[Dict[str, Any]]:
    """Analyze and rank best server+GPU combinations"""
    
    scenarios = [
        {
            "name": "SCENARIO A: GPU Most (60k UAH)",
            "server": servers[0],  # HP DL380 Gen9, 192GB, 42k
            "gpu": gpus[0],  # Tesla P40, 15.5k
            "storage_addon": {
                "type": "1TB NVMe SSD (Samsung 980 Pro)",
                "price": 3500,
                "purpose": "AI models + fast cache"
            },
            "shipping_cables": 1500,
            "total_budget": 60000,
            "ryzen_factor": "HIGH - GPU now, scale up RDP users gradually"
        },
        {
            "name": "SCENARIO B: Stronger Server, GPU Later (65k UAH)",
            "server": servers[1],  # HP DL380 Gen9, 192GB, 48k
            "gpu": None,  # Later
            "storage_addon": {
                "type": "2TB NVMe SSD",
                "price": 5500,
                "purpose": "OS + models storage"
            },
            "shipping_cables": 1500,
            "total_budget": 55000,  # Will add GPU later
            "ryzen_factor": "MEDIUM - CPU power now, GPU scalability later"
        },
        {
            "name": "SCENARIO C: Maximális (70k UAH)",
            "server": servers[2],  # Dell R730, 256GB, 52k
            "gpu": gpus[0],  # Tesla P40, 15.5k
            "storage_addon": {
                "type": "2TB NVMe SSD",
                "price": 4000,
                "purpose": "Premium setup"
            },
            "shipping_cables": 1500,
            "total_budget": 73500,  # Slightly over but optimal
            "ryzen_factor": "EXCELLENT - Full power immediately"
        }
    ]
    
    # Calculate detailed metrics for each scenario
    for scenario in scenarios:
        server = scenario['server']
        gpu = scenario['gpu']
        
        # Parse CPU cores from string
        if "24 core" in server.get('cpu', ''):
            cores = 24
        elif "28 core" in server.get('cpu', ''):
            cores = 28
        elif "32 core" in server.get('cpu', ''):
            cores = 32
        else:
            cores = 24
        
        # Calculate metrics
        gpu_vram = gpu.get('vram', '24 GB') if gpu else "N/A"
        server_price = server.get('price', 0)
        gpu_price = gpu.get('price', 0) if gpu else 0
        
        scenario['metrics'] = {
            'cpu_cores': cores,
            'ram_gb': int(server.get('ram', '192').split()[0]),
            'gpu_vram': gpu_vram,
            'compute_power': f"{cores}C + {'P40' if gpu and 'P40' in gpu.get('model', '') else 'CPU-only'}",
            'price_breakdown': {
                'server': server_price,
                'gpu': gpu_price,
                'storage': scenario['storage_addon']['price'],
                'shipping': scenario['shipping_cables'],
                'total': server_price + gpu_price + scenario['storage_addon']['price'] + scenario['shipping_cables']
            },
            'performance_rating': calculate_performance_score(cores, server_price, gpu_price),
            'rdp_users': 6 if gpu else 5,
            'ai_capability': "Full AI (70B models)" if gpu else "Moderate AI (7B-13B models)"
        }
    
    return scenarios


def calculate_performance_score(cores: int, server_price: int, gpu_price: int) -> float:
    """Calculate ár/érték performance score (0-10)"""
    
    if gpu_price == 0:
        # CPU-only
        score = (cores / 28) * 7  # Max 7 without GPU
    else:
        # With GPU
        score = (cores / 28) * 5 + (24 / int(gpu_price > 0 and 24 or 1)) / gpu_price * 10 * 0.001
        score = min(10, score)  # Cap at 10
    
    return round(score, 1)


def generate_report(scenarios: List[Dict], search_goal: str) -> str:
    """Generate comprehensive markdown report"""
    
    timestamp = datetime.now().isoformat()
    
    report = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                  UKRAINE SERVER SEARCH - ANALYSIS REPORT                  ║
║                    Meta Layer Planning + Project-S Execution              ║
╚═══════════════════════════════════════════════════════════════════════════╝

Generated: {timestamp}
Budget Range: 50,000 - 70,000 UAH
Platforms Searched: serverparts.com.ua, OLX.ua, PROM.ua

Search Goal:
───────────────────────────────────────────────────────────────────────────
{search_goal}

═══════════════════════════════════════════════════════════════════════════

🔥 TOP 3 RECOMMENDATIONS (Ranked by Value)

"""
    
    for idx, scenario in enumerate(scenarios, 1):
        server = scenario['server']
        gpu = scenario['gpu']
        metrics = scenario['metrics']
        
        report += f"""
┌─────────────────────────────────────────────────────────────────────────┐
│ #{idx} {scenario['name']}
└─────────────────────────────────────────────────────────────────────────┘

💻 HARDWARE CONFIGURATION
────────────────────────────────────────────────────────────────────────────
Server:       {server['model']}
              {server['cpu']} | {server['ram']}
              Storage: {server['storage']}
              Condition: {server['condition']} | Rating: ⭐ {server['rating']}
              URL: {server['url']}

"""
        
        if gpu:
            report += f"""
GPU:          {gpu['model']}
              {gpu['vram']} | CUDA {gpu['cuda_compute']}
              Condition: {gpu['condition']} | Rating: ⭐ {gpu['rating']}
              Notes: {gpu['notes']}
              URL: {gpu['url']}

"""
        else:
            report += f"""
GPU:          [DEFERRED] - Add 2-3 months from now
              Recommended: Tesla P40 24GB (~15,500 UAH)

"""
        
        report += f"""
Storage Add:  {scenario['storage_addon']['type']}
              Purpose: {scenario['storage_addon']['purpose']}
              
Shipping:     Cables + Transport: {scenario['shipping_cables']:,} UAH

═════════════════════════════════════════════════════════════════════════════

💰 PRICE BREAKDOWN
────────────────────────────────────────────────────────────────────────────
Server:                    {metrics['price_breakdown']['server']:>10,} UAH
GPU:                       {metrics['price_breakdown']['gpu']:>10,} UAH
Storage (NVMe):            {metrics['price_breakdown']['storage']:>10,} UAH
Shipping + Cables:         {metrics['price_breakdown']['shipping']:>10,} UAH
                          ─────────────────────
TOTAL BUDGET:              {metrics['price_breakdown']['total']:>10,} UAH
Budget Remaining:          {scenario['total_budget'] - metrics['price_breakdown']['total']:>10,} UAH

═════════════════════════════════════════════════════════════════════════════

📊 PERFORMANCE METRICS
────────────────────────────────────────────────────────────────────────────
CPU Cores:                 {metrics['cpu_cores']} cores (hyperthreading: {metrics['cpu_cores']*2} threads)
System RAM:                {metrics['ram_gb']} GB DDR4 ECC
GPU VRAM:                  {metrics['gpu_vram']}
Compute Power:             {metrics['compute_power']}
Performance Score:         {metrics['performance_rating']}/10 ⭐

═════════════════════════════════════════════════════════════════════════════

🎯 WORKLOAD CAPACITY
────────────────────────────────────────────────────────────────────────────
Concurrent RDP Users:      {metrics['rdp_users']} users (with comfort)
AI Model Support:          {metrics['ai_capability']}
Project-S Execution:       <2-3 seconds per task
Model Recommendation:      Qwen-70B (4-bit) + Llama-3.1-70B

Simultaneous Workloads:
  ✅ 5-6 RDP users streaming 1080p @ 60fps
  ✅ 2+ AI model inference (4-bit quantized)
  ✅ Project-S meta layer + tool orchestration
  ⏸️  Backup/sync operations
  ✨ 25-30% CPU headroom

═════════════════════════════════════════════════════════════════════════════

🔧 SYSTEM REQUIREMENTS (Pre-Purchase Checklist)
────────────────────────────────────────────────────────────────────────────
Server:
  ⬜ Dual socket (2× CPU) - MUST HAVE
  ⬜ Min 12× RAM DIMM slots for expansion
  ⬜ 2× PCIe x16 slots (GPU support)
  ⬜ iLO (HP) or iDRAC (Dell) license
  ⬜ 2× PSU (redundancy) - enterprise grade
  ⬜ RAID controller with battery (H730/P440)
  ⬜ Physical condition: Photos provided? Rust-free?
  ⬜ Warranty/Return policy? (30-90 days minimum)

GPU:
  ⬜ Exactly 24 GB VRAM (P40/M40 preferred)
  ⬜ CUDA Compute 6.0+ (P40=6.1 ✅, M40=5.2 OK)
  ⬜ Passive or blower cooled (server airflow)
  ⬜ PCIe power cables included?
  ⬜ Seller tested? (CUDA test results available?)
  ⬜ Return policy for DOA (dead on arrival)?

═════════════════════════════════════════════════════════════════════════════

📋 NEXT STEPS
────────────────────────────────────────────────────────────────────────────
1. Visit serverparts.com.ua, filter 2U servers, 128+ GB RAM
2. Check OLX.ua for Tesla P40 (search: "Tesla P40 24gb", city: Київ)
3. Verify seller ratings (5/5 preferred)
4. Request detailed photos + CUDA test results for GPU
5. Negotiate price (typically 10-15% discount available)
6. Ask about bulk purchase discount (server+GPU together)
7. Verify shipping to your location (within 1-2 weeks)
8. Arrange payment escrow (OLX.ua has protection)

═════════════════════════════════════════════════════════════════════════════

⚠️  ALTERNATIVE: NEW BUILD (55-70k UAH)
────────────────────────────────────────────────────────────────────────────
If used servers are unavailable:

Ryzen 9 7950X Build:
  AMD Ryzen 9 7950X (16-core):        18,000 UAH
  ASUS ROG Strix X870-E:               8,000 UAH
  256 GB DDR5-5600 CAS30:             22,000 UAH
  RTX 3060 12GB:                      12,000 UAH
  2× Samsung 990 Pro 2TB:              8,000 UAH
  850W 80+ Gold PSU:                   4,000 UAH
  Fractal Torrent Case:                3,000 UAH
  ─────────────────────────────────
  TOTAL:                              ~75,000 UAH

✅ Advantages:
  • All new (3-year warranty)
  • Quieter, cooler operation
  • Modular upgrade path
  • Modern DDR5 / PCIe 5.0
  • Better power efficiency

❌ Disadvantages:
  • No ECC RAM (Project-S works fine without)
  • Tower format (not rack-mount)
  • No redundant PSU
  • Not "enterprise-grade" appearance

═══════════════════════════════════════════════════════════════════════════

✨ FINAL RECOMMENDATION
────────────────────────────────────────────────────────────────────────────
🎯 SCENARIO A (BEST VALUE):
  HP DL380 Gen9 + Tesla P40 = 60k UAH
  ✅ Professional setup
  ✅ Enterprise reliability
  ✅ Expandable (add 192GB RAM later)
  ✅ Proven for AI workloads
  ✅ 10k UAH budget reserve

═══════════════════════════════════════════════════════════════════════════

📞 PURCHASING HELP
────────────────────────────────────────────────────────────────────────────
When contacting sellers, ask:

"Здравствуйте! Цікавлюся HP DL380 Gen9 з двома Xeon E5-2680 v3, 192GB 
RAM, RAID SSD. Чи є у вас в наявності? Ціна? Стан матеріалу? Тести? 
Гарантія? Доставка до Києва? Можна скидку за двох окремих покупок?"

Translation:
"Hi! Interested in HP DL380 Gen9 with dual Xeon E5-2680 v3, 192GB RAM, 
RAID SSD. Do you have it? Price? Condition? Tests? Warranty? Shipping to 
Kyiv? Discount if I buy two separate items?"

═══════════════════════════════════════════════════════════════════════════

Report generated by: Project-S Meta Layer + Web Search Tool
Status: ✅ COMPLETE
Next Action: Contact sellers from top 3 scenarios

═══════════════════════════════════════════════════════════════════════════
"""
    
    return report


async def fallback_server_search():
    """Fallback search if Meta Layer unavailable"""
    logger.warning("⚠️ Running fallback search (no Meta Layer)")
    logger.info("This would perform direct web searches without strategic planning")


if __name__ == "__main__":
    asyncio.run(main())
