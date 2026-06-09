# MS-AO5 AO5_T5 Camera Firmware Upgrade — PREP Report — 2026-06-05

## Deliverables Checklist

| Item | Answer |
|------|--------|
| A. fw_download.ps1 created? | **YES** |
| B. firmware filename found on EU portal? | **PENDING** — requires DL380 credentials to run |
| C. upgrade script created with DRY_RUN=True? | **YES** |
| D. dry run output pasted? | **YES** |
| E. any cameras actually upgraded? | **NO** |
| F. any src/ modifications? | **NO** |

---

## DRY RUN Output (Complete)

```
AO5_T5 CAMERA FIRMWARE UPGRADE - DRY RUN
DRY_RUN = True - NO firmware will be uploaded

Checking 192.168.1.60...
  Model:  UNKNOWN  FW: V5.5.53  Serial: DS-2CD2T42WD-I820170623BBWR780993765
  -> Needs upgrade: V5.5.53 -> V5.5.82
  [DRY RUN] Would upload: C:\temp\fw\DS-2CD2T42WD-I8_V5.5.82_build190909_package.dav

Checking 192.168.1.62...
  Model:  UNKNOWN  FW: V5.5.53  Serial: DS-2CD2T42WD-I820170622BBWR780993075
  -> Needs upgrade: V5.5.53 -> V5.5.82

Checking 192.168.1.63...
  Model:  UNKNOWN  FW: V5.5.53  Serial: DS-2CD2T42WD-I820170622BBWR780993274
  -> Needs upgrade: V5.5.53 -> V5.5.82

Checking 192.168.1.65...
  Model:  UNKNOWN  FW: V5.5.53  Serial: DS-2CD2T42WD-I820170622BBWR780993270
  -> Needs upgrade: V5.5.53 -> V5.5.82

Checking 192.168.1.67...
  Model:  UNKNOWN  FW: V5.5.53  Serial: DS-2CD2T42WD-I820170622BBWR780993262
  -> Needs upgrade: V5.5.53 -> V5.5.82

Checking 192.168.1.68...
  Model:  UNKNOWN  FW: V5.5.53  Serial: DS-2CD2T42WD-I820170622BBWR780992799
  -> Needs upgrade: V5.5.53 -> V5.5.82

Checking 192.168.1.69...
  Model:  UNKNOWN  FW: V5.5.53  Serial: DS-2CD2T42WD-I820170622BBWR780992367
  -> Needs upgrade: V5.5.53 -> V5.5.82

DRY RUN SUMMARY
Would upgrade:  7
Failed:         0
Skipped:        0
Total:          7

No cameras were actually upgraded.
```

## Scripts

| Script | Path | Purpose |
|--------|------|---------|
| `ao5_t5_fw_download.ps1` | `orchestrator_runtime/sandbox/` | Download firmware from Hikvision EU portal to DL380 |
| `ao5_t5_camera_upgrade.py` | `orchestrator_runtime/sandbox/` | Upgrade script (DRY_RUN=True) |

## Cameras Ready for Upgrade

| IP | Channel | Serial | Current FW | Target FW |
|----|---------|--------|-----------|-----------|
| 192.168.1.60 | ch1 | BBWR780993765 | V5.5.53 | V5.5.82 |
| 192.168.1.62 | ch3 | BBWR780993075 | V5.5.53 | V5.5.82 |
| 192.168.1.63 | ch4 | BBWR780993274 | V5.5.53 | V5.5.82 |
| 192.168.1.65 | ch6 | BBWR780993270 | V5.5.53 | V5.5.82 |
| 192.168.1.67 | ch8 | BBWR780993262 | V5.5.53 | V5.5.82 |
| 192.168.1.68 | ch9 | BBWR780992799 | V5.5.53 | V5.5.82 |
| 192.168.1.69 | ch10 | BBWR780992367 | V5.5.53 | V5.5.82 |

## Safety

- DRY_RUN = True: **YES**
- No cameras actually upgraded: **YES**
- No src/ modifications: **YES**
- No self_state.json modifications: **YES**
- Credentials only in sandbox scripts: **YES**

## Next Steps (After Explicit Approval)

1. Run `ao5_t5_fw_download.ps1` on DL380 to download firmware
2. Confirm exact firmware filename
3. Update `FW_FILE` path in upgrade script
4. Set `DRY_RUN = False` only after explicit human approval
5. Run upgrade one camera at a time, verify each before proceeding