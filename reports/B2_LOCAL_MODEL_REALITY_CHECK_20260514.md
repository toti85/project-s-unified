# Strategic AI Report

Generated: 2026-05-14T00:52:15.340504

## Task
Search the web for information about Qwen3.6-35B-A3B (a May 2026 MoE model with 35B params / 3B active) and other currently available 2026 local models including Gemma 4-31B, Llama 4 Scout, Mistral Small 3.1. Compare their coding and agentic task performance, VRAM requirements, and feasibility on a Tesla M60 16GB server. Search and find the SWE-bench scores and token throughput for each model. Write a comprehensive markdown decision memo to the file C:\ProjectS-Unified\reports\B2_LOCAL_MODEL_REALITY_CHECK_20260514.md that contains: 1) candidate models list with Qwen3.6-35B-A3B included, 2) comparison table of coding/agentic usefulness, deployability, hardware fit and integration risk, 3) distinction of confirmed facts vs assumptions, 4) sources used, 5) concrete recommendation: integrate now OR test later OR defer and stay cloud-first for Project-S on OpenRouter.

## Results
[web_search result]:
Tool web_search executed successfully: Web search results for: Search the web for information about Qwen3.6-35B-A3B (a May 2026 MoE model with 35B params / 3B active) and other currently available 2026 local models including Gemma 4-31B, Llama 4 Scout, Mistral Small 3.1. Compare their coding and agentic task performance, VRAM requirements, and feasibility on a Tesla M60 16GB server. Search and find the SWE-bench scores and token throughput for each model. Write a comprehensive markdown decision memo to the file C:\ProjectS-Unified\reports\B2_LOCAL_MODEL_REA

1. Qwen3.6 35B A3B: Specifications and GPU VRAM Requirements
   URL: https://apxml.com/models/qwen36-35b-a3b
   Qwen3.6 35B A3B Qwen3.6-35B-A3B is Alibaba's open-source hybrid MoE model with 35B total parameters and only 3B active per token.

2. How to run Qwen3.6-35B-A3B locally — the coding MoE that beats models ...
   URL: https://dev.to/purpledoubled/how-to-run-qwen36-35b-a3b-locally-the-coding-moe-that-beats-models-10x-its-active-size-3pbh
   Why this model matters The numbers speak for themselves: 73.4 on SWE-bench Verified — this is an agentic coding benchmark where the model autonomously fixes real GitHub issues. For reference, Gemma4-31B (a dense model with all 31B params active) scores 17.4. Qwen3.6 scores 4x higher with 10x fewer active parameters.

3. Qwen3.6-35B-A3B: 73.4% SWE-Bench, Runs Locally
   URL: https://www.buildfastwithai.com/blogs/qwen3-6-35b-a3b-review
   Alibaba's Qwen3.6-35B-A3B scores 73.4% on SWE-bench with 3B active params. Full benchmarks, Gemma 4 comparison, and how to run it locally in 2026.

4. Qwen 3.6 Complete Guide: 27B Dense, 35B-A3B MoE, and Which to Use
   URL: https://insiderllm.com/guides/qwen-3-6-local-ai-guide/
   Qwen 3.6 landed in two open-weight flavors: 27B dense and 35B-A3B MoE. Benchmarks, hardware fit, and which variant to run on your GPU.

5. Qwen3.6-35B: 7 Critical Facts About Qwen's New Open-Weight…
   URL: https://www.progressiverobot.com/2026/04/17/qwen3-6-35b/
   Qwen3.6-35B is the new open-weight release from Qwen for developers who want stronger agentic coding, long-context reasoning, and multimodal capability without moving up to a much larger dense model. The official checkpoint carries an A3B suffix, but the simpler search term is already how many developers are referring to the release. In Qwen's official launch post, the team presents the ...

6. Qwen 3.6: 35B vs 27B comparison - benchmark results
   URL: https://zoliben.com/en/posts/2026-04-23-qwen-36-35b-vs-27b-benchmark-results/
   I finally summed up all the Qwen 3.6 model test results I gathered over the past few days. I compared two models in detail: the Qwen3.6-35B-A3B (MoE, hybrid attention/delta) and the Qwen3.6-27B (dense, hybrid attention/delta). I ran both with turbo3 KV cache compression on an RTX 4090 as a llama.cpp server. If I had to summarize briefly: the 35B-A3B is 3-4x faster in everything, but the 27B ...

7. Alibaba Open Sources Qwen3.6-35B-A3B: A 30 Billion Activated Parameter ...
   URL: https://www.aibase.com/news/27222
   The Alibaba Qwen large model team officially open-sourced the sparse mixture-of-experts (MoE) model Qwen3.6-35B-A3B on April 16, 2026, marking a key breakthrough in lightweight models within the field of intelligent agent programming. The model has a total of 35 billion parameters.

8. Qwen3.6-35B Drops: Agentic Coding Gets a Major Upgrade
   URL: https://stable-learn.com/en/qwen36-35b-a3b-release/
   Qwen3.6-35B-A3B launched on April 16. Despite the minor version bump from 3.5 to 3.6, this release delivers substantial improvements for developers— agentic coding capabilities reach new heights, and thinking preservation finally solves the context-loss problem.

9. Qwen3.6-35B-A3B Is Now Open Source - AI You Need
   URL: https://www.aiyouneed.com/en/news/qwen36-35b-a3b-is-now-open-source/
   Qwen has open-sourced Qwen3.6-35B-A3B following the launch of Qwen3.6-Plus. The MoE model combines 35 billion total parameters with only 3 billion active parameters and is being positioned around agentic coding and multimodal reasoning.

10. Qwen Team Open-Sources Qwen3.6-35B-A3B: A Sparse MoE Vision-Language ...
   URL: https://www.marktechpost.com/2026/04/16/qwen-team-open-sources-qwen3-6-35b-a3b-a-sparse-moe-vision-language-model-with-3b-active-parameters-and-agentic-coding-capabilities/
   Qwen3.6-35B-A3B is a Causal Language Model with Vision Encoder, trained through both pre-training and post-training stages, with 35 billion total parameters and 3 billion activated. Its MoE layer contains 256 experts in total, with 8 routed experts and 1 shared expert activated per token. The architecture introduces an unusual hidden layout worth understanding: the model uses a pattern of 10 ...


[web_scraper result]:
Tool web_scraper executed successfully: [{'url': 'https://apxml.com/models/qwen36-35b-a3b', 'scraped_at': '2026-05-14T00:52:15.074937', 'title': 'Qwen3.6 35B A3B', 'description': 'Technical specifications and GPU VRAM requirements for Qwen3.6 35B A3B.', 'links': ['https://apxml.com/models', 'https://apxml.com/models/?family=86', 'https://apxml.com/models/qwen36-35b-a3b', 'https://livebench.ai/#/?Reasoning=a', 'https://apxml.com/model-transparency', 'https://apxml.com/tools/vram-calculator', 'https://qwen.ai/blog?id=qwen3.6-35b-a3b', 'https://huggingface.co/Qwen/Qwen3.6-35B-A3B', 'https://apxml.com/about', 'https://apxml.com/contact'], 'images': ['https://apxml.com/icons/apx-logo-smaller.webp', 'https://apxml.com/icons/apx-logo-smaller.webp']}]
