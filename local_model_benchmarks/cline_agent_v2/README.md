# Isolated Cline-Agent Benchmark v2

This sandbox measures whether a local coding model can handle tasks similar to
the executor role without reading or changing active Project-S development.

## Isolation guarantees

- All task inputs are fictional fixtures under this directory.
- The runner sends fixture text to the model; it grants no filesystem tools.
- Model responses and scores are written only to `results/`.
- No inbox, outbox, governance, `src/`, or production file is referenced.
- The patch task asks for text output only and never applies the patch.

## Cases

1. `architecture_plan`: produce a safe advisory integration plan.
2. `code_review`: find correctness and concurrency defects in a queue module.
3. `patch_generation`: return a constrained unified diff for a small module.

## Run

From PowerShell, create the DL380 credential in memory and run:

```powershell
$credential = Get-Credential Administrator
.\run_remote_benchmark.ps1 -Credential $credential
```

The remote model must be available at `http://127.0.0.1:8098`. The runner
uses WinRM only to call that loopback endpoint on the DL380.

## Output

Each run creates a timestamped directory under `results/` containing:

- one raw response per case;
- `summary.json` with latency, rubric checks, and pass/fail verdicts.

## DL380 development profiles

The deployed runtime manager is mirrored at:

`scripts/model_runtime_manager.ps1`

It exposes mutually exclusive, loopback-only profiles:

```powershell
# Run on DL380
F:\ModelVault\scripts\model_runtime_manager.ps1 -ProfileName coder
F:\ModelVault\scripts\model_runtime_manager.ps1 -ProfileName planner
F:\ModelVault\scripts\model_runtime_manager.ps1 -ProfileName status
F:\ModelVault\scripts\model_runtime_manager.ps1 -ProfileName stop
```

`coder` serves Qwen2.5-Coder-14B on `127.0.0.1:8098`. `planner` serves
Qwen3.6 through the non-thinking compatibility proxy on `127.0.0.1:8097`.
Only one generative profile runs at a time. The boot default is `coder`.

Development permissions and promotion gates are machine-readable in
`config/local_model_development_policy.json`.
