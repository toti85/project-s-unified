# SANDBOX_TASK_001: Markdown File Lister

**Task ID:** SANDBOX_TASK_001
**Run ID:** FA1_001
**Created:** 2026-05-24
**Difficulty:** Simple
**Expected Duration:** Less than 15 minutes

---

## Task Description

Create a small Python helper script that lists all markdown files in a given folder.

## Deliverables

### 1. Helper Script: `sandbox/md_lister.py`

A Python script containing a function:

```python
def list_markdown_files(folder_path: str) -> list[str]:
    """
    List all .md files in the given folder (non-recursive).

    Args:
        folder_path: Path to the directory to scan

    Returns:
        Sorted list of markdown filenames (not full paths)

    Raises:
        FileNotFoundError: If folder_path does not exist
        NotADirectoryError: If folder_path is not a directory
    """
    ...
```

**Requirements:**
- Accepts a folder path (string)
- Returns a sorted list of `.md` filenames
- Non-recursive (top-level only)
- Raises `FileNotFoundError` if folder doesn't exist
- Raises `NotADirectoryError` if path is not a directory
- No external dependencies (stdlib only)

### 2. Unit Tests: `sandbox/test_md_lister.py`

Exactly 3 unit tests using Python's `unittest` framework:

| Test | Description |
|------|-------------|
| `test_list_md_files_in_temp_dir` | Create a temp dir with mixed files, verify only .md files returned |
| `test_empty_directory` | Verify empty list returned for directory with no .md files |
| `test_nonexistent_directory` | Verify FileNotFoundError is raised for invalid path |

## Constraints

- **WORK ONLY IN:** `C:\ProjectS-Unified\orchestrator_runtime\sandbox\`
- **DO NOT MODIFY:** Any files in `C:\ProjectS-Unified\`
- **DO NOT MODIFY:** Any config, router, or server files
- **NO NETWORK:** No external network calls required or allowed

## Acceptance Criteria

- [ ] `md_lister.py` exists in sandbox
- [ ] `test_md_lister.py` exists in sandbox with exactly 3 tests
- [ ] All 3 tests pass when run with `python -m unittest sandbox/test_md_lister.py`
- [ ] Function handles edge cases (empty dir, nonexistent dir)
- [ ] No files outside sandbox were modified

## Testing

Run tests with:
```bash
cd C:\ProjectS-Unified\orchestrator_runtime
python -m unittest sandbox/test_md_lister.py -v
```

Expected output: All 3 tests PASS

## Final Output

After completing the task, write a report to:
```
C:\ProjectS-Unified\orchestrator_runtime\cline_outbox\last_output.md
```

Include:
- Files created (full paths)
- Test results (copy paste the output)
- Any issues encountered