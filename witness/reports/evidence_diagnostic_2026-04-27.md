# Evidence Diagnostic Report

**Generálva:** 2026-04-27T20:56:45Z
**Forrás:** `C:\ProjectS-Unified\memory\intelligence\meta_evidence.jsonl`
**Scan idő:** 5.05 s

## Összesítő

| Metrika | Érték |
|---------|-------|
| Összes rekord | 403,868 |
| Parse hibák | 0 |
| Összes napok száma | 5 |

### Event típusok

| Event típus | Db |
|-------------|-----|
| `goal_started` | 201,835 |
| `plan_selected` | 201,851 |
| `execution_done` | 59 |
| `validation_done` | 59 |
| `replan_triggered` | 25 |
| `goal_completed` | 37 |
| `goal_failed` | 2 |

## a) Időbeli Eloszlás

### Top 10 nap (rekordszám szerint)

| Nap | Összes | goal_started | goal_completed | goal_failed |
|-----|--------|:------------:|:--------------:|:-----------:|
| 2026-01-14 | 403,636 | 201,798 | 2 | 1 |
| 2026-01-16 | 125 | 25 | 25 | 0 |
| 2026-01-15 | 92 | 9 | 7 | 1 |
| 2026-02-18 | 10 | 2 | 2 | 0 |
| 2026-02-19 | 5 | 1 | 1 | 0 |

### Teljes napi bontás (kronológiai sorrendben)

| Nap | Összes | goal_started | goal_completed | goal_failed |
|-----|--------|:------------:|:--------------:|:-----------:|
| 2026-01-14 | 403,636 | 201,798 | 2 | 1 |
| 2026-01-15 | 92 | 9 | 7 | 1 |
| 2026-01-16 | 125 | 25 | 25 | 0 |
| 2026-02-18 | 10 | 2 | 2 | 0 |
| 2026-02-19 | 5 | 1 | 1 | 0 |

## b) Goal ID Mintázat

**Összes goal_id-t érintő esemény:** 403,868
**Reservoir mérete:** 100 (véletlenszerű minta)

### Prefix eloszlás a mintában

| Prefix | Minta-db |
|--------|----------|
| `<date_based>` | 100 |

### Mintavételezett goal_id-k (100 db)

```
20260114_235926_kkobir
20260114_234640_dn2299
20260114_235958_xsda4o
20260114_235952_ehlt9x
20260114_235955_2uyly5
20260114_235254_fm1zcu
20260114_235908_to749b
20260114_235516_jg1x27
20260114_235903_r71kes
20260115_001734_jb9hkx
20260115_001645_7ngkh9
20260115_001650_e95lk8
20260114_235953_ohaxde
20260114_235913_px35xs
20260114_234652_7wgzri
20260114_235948_ccaosw
20260115_001613_wi4pts
20260114_235043_orx8c8
20260115_001729_lwnbms
20260114_235124_3z9egd
20260115_001616_zc2rfs
20260114_235905_xpp4hi
20260115_001545_dfl74l
20260115_001713_pnqql9
20260114_235956_tvxzt0
20260114_234647_iaekm3
20260115_001533_5sudzv
20260115_001455_5ypkia
20260115_001559_yg1qjm
20260115_001551_21utu4
20260115_001638_p0ak4b
20260115_001530_sybypd
20260115_001557_b036mg
20260115_001521_cgsscn
20260115_001611_2it593
20260115_001605_hd6k33
20260114_235940_7w4h92
20260115_001650_illk6r
20260114_235903_rmr6zu
20260114_235947_dyr3vq
20260115_001650_d65ckp
20260114_235605_4xxlwh
20260114_235859_tladg0
20260115_001545_hn01wk
20260114_235631_fa94di
20260115_001618_21dea6
20260114_235624_ux73ur
20260115_001621_zrqqry
20260114_235549_1zhws5
20260115_001644_asnklc
20260114_235956_2v7dfc
20260114_235935_nj5msx
20260114_235958_fxc0ws
20260114_235948_y2ens0
20260114_234719_fcr9id
20260114_235917_saqu5l
20260114_235611_scdaoo
20260114_234704_n2ts84
20260115_001504_5l3ofh
20260115_001515_cbg3v7
20260114_235103_ei8qtu
20260114_235647_5bp06n
20260115_001551_im6sjc
20260115_001659_qgw0k8
20260115_001521_l3w27c
20260114_235105_wlq6cl
20260115_001501_htoc03
20260115_001550_5vcd1v
20260114_235558_ionz2k
20260114_235912_2vdzv7
20260114_235544_pzm73t
20260115_001503_b4m5zp
20260114_235929_ns6619
20260115_001724_jxhxi2
20260114_235250_wkuof5
20260114_235558_2pbggh
20260115_001711_44fkkn
20260114_235535_5uwxb7
20260114_235923_lpb2pe
20260115_001640_30yxes
20260114_235545_85g44w
20260115_001639_at8wo7
20260115_001627_bmz8ff
20260115_001515_498232
20260114_234713_2yggo0
20260115_001532_pbgjq4
20260114_234701_59b3ky
20260115_001736_0fxvza
20260115_001509_044aom
20260115_001539_ka4d7x
20260115_001556_mmpv9g
20260115_001540_p49o43
20260115_001628_kfeyvi
20260115_001529_7xdtqu
20260114_235904_8twfx8
20260115_001713_n40fxp
20260114_235311_m75bry
20260115_001650_pfm7ji
20260114_234659_vadkr9
20260115_001628_8sqtb6
```

### A 37 db goal_completed goal_id-je (valódi sikerek)

```
20260115_002049_1lczll
20260115_002917_0kulvq
20260115_075059_s4qaq7
20260115_075333_4tmhue
20260115_083708_fxm2n3
20260115_083826_a4zzct
20260115_084029_xdgsrv
20260115_085142_1dcpnl
20260115_090010_d5iw1s
20260116_195116_rbf7g6
20260116_200949_jl04om
20260116_201058_gkog2y
20260116_201201_jijb9o
20260116_201403_lis86x
20260116_201433_9qefq0
20260116_201747_tm4j9c
20260116_201852_kleud2
20260116_202607_z22csk
20260116_202705_zt513z
20260116_202749_2qbuob
20260116_205739_7zjwno
20260116_205758_2jnuxc
20260116_205927_1bwy1r
20260116_210410_x75a7p
20260116_210433_bqneu6
20260116_210604_bdluxu
20260116_210702_eb3bzu
20260116_210725_oq9lu3
20260116_210856_f3g282
20260116_212156_02p8fh
20260116_212221_hihh9r
20260116_212348_6ufgxm
20260116_215359_j0zyv2
20260116_215601_9n63c7
20260218_122512_4t14y7
20260218_122802_8r3ebz
20260219_080122_knyew9
```

## c) Source-alapú Bontás (első 1000 rekord)

### Top-level kulcsok

| Kulcs | Előfordulás |
|-------|-------------|
| `timestamp` | 1000 |
| `event_type` | 1000 |
| `data` | 1000 |

### `data.*` kulcsok

| data.kulcs | Előfordulás |
|------------|-------------|
| `goal_id` | 501 |
| `goal` | 500 |
| `config` | 500 |
| `iteration` | 499 |
| `decision` | 499 |
| `constraints` | 499 |
| `reason` | 1 |
| `iterations` | 1 |

### Source / module / script / origin értékek

*Nem található `source`, `module`, `script`, `origin`, `caller`, `agent` mező az első 1000 rekordban.*

## d) Goal Életciklus Párosítás

> Megjegyzés: a `plan_selected`, `execution_done`, `validation_done` eseményekben nincs `goal_id` mező — a párosítás szekvenciális kontextussal történt (utolsó `goal_started` goal_id-ja).

```
goal_started              :  201,835
  ↳ kapott plan_selected  :  200,878  (99.5% of started)

plan_selected (egyedi id) :  200,878
  ↳ kapott execution_done :       40  (0.0% of planned)

execution_done (egyedi)   :       40
  ↳ kapott validation_done:       40  (100.0% of executed)

validation_done (egyedi)  :       40
  ↳ terminal állapotba ért:       38  (95.0% of validated)

goal_completed (egyedi)   :       37
goal_failed    (egyedi)   :        2
összes terminal           :       39
  ebből goal_started-ból  :       39  (0.0% of started)
```

### Pipeline drop-off vízesés

| Fázis | Egyedi goal_id-k | Δ az előzőhöz |
|-------|:---------------:|:--------------:|
| `goal_started` | 201,835 | — |
| `plan_selected` | 200,878 | 99.5% |
| `execution_done` | 40 | 0.0% |
| `validation_done` | 40 | 100.0% |
| `terminal (completed|failed)` | 39 | 97.5% |

**Magyarázat:** Ha a `plan_selected` << `goal_started`, akkor a célok nagy része tervezési fázisban omlik le (pl. consensus hiba).

## e) Az Utolsó 100 Rekord

| # | timestamp | event_type | goal_id |
|---|-----------|------------|---------|
| 1 | 2026-01-16T18:26:07 | `goal_started` | 20260116_202607_z22csk |
| 2 | 2026-01-16T18:26:07 | `plan_selected` | 20260116_202607_z22csk |
| 3 | 2026-01-16T18:26:36 | `execution_done` | 20260116_202607_z22csk |
| 4 | 2026-01-16T18:26:36 | `validation_done` | 20260116_202607_z22csk |
| 5 | 2026-01-16T18:26:36 | `goal_completed` | 20260116_202607_z22csk |
| 6 | 2026-01-16T18:27:05 | `goal_started` | 20260116_202705_zt513z |
| 7 | 2026-01-16T18:27:05 | `plan_selected` | 20260116_202705_zt513z |
| 8 | 2026-01-16T18:27:29 | `execution_done` | 20260116_202705_zt513z |
| 9 | 2026-01-16T18:27:29 | `validation_done` | 20260116_202705_zt513z |
| 10 | 2026-01-16T18:27:29 | `goal_completed` | 20260116_202705_zt513z |
| 11 | 2026-01-16T18:27:49 | `goal_started` | 20260116_202749_2qbuob |
| 12 | 2026-01-16T18:27:49 | `plan_selected` | 20260116_202749_2qbuob |
| 13 | 2026-01-16T18:28:14 | `execution_done` | 20260116_202749_2qbuob |
| 14 | 2026-01-16T18:28:14 | `validation_done` | 20260116_202749_2qbuob |
| 15 | 2026-01-16T18:28:14 | `goal_completed` | 20260116_202749_2qbuob |
| 16 | 2026-01-16T18:57:39 | `goal_started` | 20260116_205739_7zjwno |
| 17 | 2026-01-16T18:57:39 | `plan_selected` | 20260116_205739_7zjwno |
| 18 | 2026-01-16T18:57:58 | `execution_done` | 20260116_205739_7zjwno |
| 19 | 2026-01-16T18:57:58 | `validation_done` | 20260116_205739_7zjwno |
| 20 | 2026-01-16T18:57:58 | `goal_completed` | 20260116_205739_7zjwno |
| 21 | 2026-01-16T18:57:58 | `goal_started` | 20260116_205758_2jnuxc |
| 22 | 2026-01-16T18:57:58 | `plan_selected` | 20260116_205758_2jnuxc |
| 23 | 2026-01-16T18:59:27 | `execution_done` | 20260116_205758_2jnuxc |
| 24 | 2026-01-16T18:59:27 | `validation_done` | 20260116_205758_2jnuxc |
| 25 | 2026-01-16T18:59:27 | `goal_completed` | 20260116_205758_2jnuxc |
| 26 | 2026-01-16T18:59:27 | `goal_started` | 20260116_205927_1bwy1r |
| 27 | 2026-01-16T18:59:27 | `plan_selected` | 20260116_205927_1bwy1r |
| 28 | 2026-01-16T18:59:48 | `execution_done` | 20260116_205927_1bwy1r |
| 29 | 2026-01-16T18:59:48 | `validation_done` | 20260116_205927_1bwy1r |
| 30 | 2026-01-16T18:59:48 | `goal_completed` | 20260116_205927_1bwy1r |
| 31 | 2026-01-16T19:04:10 | `goal_started` | 20260116_210410_x75a7p |
| 32 | 2026-01-16T19:04:10 | `plan_selected` | 20260116_210410_x75a7p |
| 33 | 2026-01-16T19:04:33 | `execution_done` | 20260116_210410_x75a7p |
| 34 | 2026-01-16T19:04:33 | `validation_done` | 20260116_210410_x75a7p |
| 35 | 2026-01-16T19:04:33 | `goal_completed` | 20260116_210410_x75a7p |
| 36 | 2026-01-16T19:04:33 | `goal_started` | 20260116_210433_bqneu6 |
| 37 | 2026-01-16T19:04:33 | `plan_selected` | 20260116_210433_bqneu6 |
| 38 | 2026-01-16T19:06:04 | `execution_done` | 20260116_210433_bqneu6 |
| 39 | 2026-01-16T19:06:04 | `validation_done` | 20260116_210433_bqneu6 |
| 40 | 2026-01-16T19:06:04 | `goal_completed` | 20260116_210433_bqneu6 |
| 41 | 2026-01-16T19:06:04 | `goal_started` | 20260116_210604_bdluxu |
| 42 | 2026-01-16T19:06:04 | `plan_selected` | 20260116_210604_bdluxu |
| 43 | 2026-01-16T19:06:34 | `execution_done` | 20260116_210604_bdluxu |
| 44 | 2026-01-16T19:06:34 | `validation_done` | 20260116_210604_bdluxu |
| 45 | 2026-01-16T19:06:34 | `goal_completed` | 20260116_210604_bdluxu |
| 46 | 2026-01-16T19:07:02 | `goal_started` | 20260116_210702_eb3bzu |
| 47 | 2026-01-16T19:07:02 | `plan_selected` | 20260116_210702_eb3bzu |
| 48 | 2026-01-16T19:07:25 | `execution_done` | 20260116_210702_eb3bzu |
| 49 | 2026-01-16T19:07:25 | `validation_done` | 20260116_210702_eb3bzu |
| 50 | 2026-01-16T19:07:25 | `goal_completed` | 20260116_210702_eb3bzu |
| 51 | 2026-01-16T19:07:25 | `goal_started` | 20260116_210725_oq9lu3 |
| 52 | 2026-01-16T19:07:25 | `plan_selected` | 20260116_210725_oq9lu3 |
| 53 | 2026-01-16T19:08:56 | `execution_done` | 20260116_210725_oq9lu3 |
| 54 | 2026-01-16T19:08:56 | `validation_done` | 20260116_210725_oq9lu3 |
| 55 | 2026-01-16T19:08:56 | `goal_completed` | 20260116_210725_oq9lu3 |
| 56 | 2026-01-16T19:08:56 | `goal_started` | 20260116_210856_f3g282 |
| 57 | 2026-01-16T19:08:56 | `plan_selected` | 20260116_210856_f3g282 |
| 58 | 2026-01-16T19:09:25 | `execution_done` | 20260116_210856_f3g282 |
| 59 | 2026-01-16T19:09:25 | `validation_done` | 20260116_210856_f3g282 |
| 60 | 2026-01-16T19:09:25 | `goal_completed` | 20260116_210856_f3g282 |
| 61 | 2026-01-16T19:21:56 | `goal_started` | 20260116_212156_02p8fh |
| 62 | 2026-01-16T19:21:56 | `plan_selected` | 20260116_212156_02p8fh |
| 63 | 2026-01-16T19:22:21 | `execution_done` | 20260116_212156_02p8fh |
| 64 | 2026-01-16T19:22:21 | `validation_done` | 20260116_212156_02p8fh |
| 65 | 2026-01-16T19:22:21 | `goal_completed` | 20260116_212156_02p8fh |
| 66 | 2026-01-16T19:22:21 | `goal_started` | 20260116_212221_hihh9r |
| 67 | 2026-01-16T19:22:21 | `plan_selected` | 20260116_212221_hihh9r |
| 68 | 2026-01-16T19:23:48 | `execution_done` | 20260116_212221_hihh9r |
| 69 | 2026-01-16T19:23:48 | `validation_done` | 20260116_212221_hihh9r |
| 70 | 2026-01-16T19:23:48 | `goal_completed` | 20260116_212221_hihh9r |
| 71 | 2026-01-16T19:23:48 | `goal_started` | 20260116_212348_6ufgxm |
| 72 | 2026-01-16T19:23:48 | `plan_selected` | 20260116_212348_6ufgxm |
| 73 | 2026-01-16T19:24:16 | `execution_done` | 20260116_212348_6ufgxm |
| 74 | 2026-01-16T19:24:16 | `validation_done` | 20260116_212348_6ufgxm |
| 75 | 2026-01-16T19:24:16 | `goal_completed` | 20260116_212348_6ufgxm |
| 76 | 2026-01-16T19:53:59 | `goal_started` | 20260116_215359_j0zyv2 |
| 77 | 2026-01-16T19:53:59 | `plan_selected` | 20260116_215359_j0zyv2 |
| 78 | 2026-01-16T19:54:26 | `execution_done` | 20260116_215359_j0zyv2 |
| 79 | 2026-01-16T19:54:26 | `validation_done` | 20260116_215359_j0zyv2 |
| 80 | 2026-01-16T19:54:26 | `goal_completed` | 20260116_215359_j0zyv2 |
| 81 | 2026-01-16T19:56:01 | `goal_started` | 20260116_215601_9n63c7 |
| 82 | 2026-01-16T19:56:01 | `plan_selected` | 20260116_215601_9n63c7 |
| 83 | 2026-01-16T19:56:25 | `execution_done` | 20260116_215601_9n63c7 |
| 84 | 2026-01-16T19:56:25 | `validation_done` | 20260116_215601_9n63c7 |
| 85 | 2026-01-16T19:56:25 | `goal_completed` | 20260116_215601_9n63c7 |
| 86 | 2026-02-18T10:25:12 | `goal_started` | 20260218_122512_4t14y7 |
| 87 | 2026-02-18T10:25:12 | `plan_selected` | 20260218_122512_4t14y7 |
| 88 | 2026-02-18T10:25:46 | `execution_done` | 20260218_122512_4t14y7 |
| 89 | 2026-02-18T10:25:46 | `validation_done` | 20260218_122512_4t14y7 |
| 90 | 2026-02-18T10:25:46 | `goal_completed` | 20260218_122512_4t14y7 |
| 91 | 2026-02-18T10:28:02 | `goal_started` | 20260218_122802_8r3ebz |
| 92 | 2026-02-18T10:28:02 | `plan_selected` | 20260218_122802_8r3ebz |
| 93 | 2026-02-18T10:28:24 | `execution_done` | 20260218_122802_8r3ebz |
| 94 | 2026-02-18T10:28:24 | `validation_done` | 20260218_122802_8r3ebz |
| 95 | 2026-02-18T10:28:24 | `goal_completed` | 20260218_122802_8r3ebz |
| 96 | 2026-02-19T06:01:22 | `goal_started` | 20260219_080122_knyew9 |
| 97 | 2026-02-19T06:01:22 | `plan_selected` | 20260219_080122_knyew9 |
| 98 | 2026-02-19T06:01:59 | `execution_done` | 20260219_080122_knyew9 |
| 99 | 2026-02-19T06:01:59 | `validation_done` | 20260219_080122_knyew9 |
| 100 | 2026-02-19T06:01:59 | `goal_completed` | 20260219_080122_knyew9 |

### Utolsó 10 rekord — teljes tartalom

```json
{"timestamp": "2026-02-18T10:28:02.175254", "event_type": "goal_started", "data": {"goal_id": "20260218_122802_8r3ebz", "goal": "Create a file named 'meta_layer_result.txt' on the desktop with the current timestamp and a message confirming meta layer execution", "config": {"max_iters": 5, "step_timeout_sec": 120, "risk_budget_failures": 2, "progress_required": true}}}
{"timestamp": "2026-02-18T10:28:02.175254", "event_type": "plan_selected", "data": {"goal_id": "20260218_122802_8r3ebz", "iteration": 1, "decision": {"decision": "approved", "consensus": "unanimous", "approval_ratio": 1.0, "avg_confidence": 70.0}, "constraints": {}}}
{"timestamp": "2026-02-18T10:28:24.141489", "event_type": "execution_done", "data": {"goal_id": "20260218_122802_8r3ebz", "iteration": 1, "execution_status": "success", "execution_time_ms": null}}
{"timestamp": "2026-02-18T10:28:24.141489", "event_type": "validation_done", "data": {"goal_id": "20260218_122802_8r3ebz", "iteration": 1, "validation_passed": false, "consensus_type": "failed", "confidence": 0, "critical_issues": 0, "total_issues": 0}}
{"timestamp": "2026-02-18T10:28:24.156804", "event_type": "goal_completed", "data": {"goal_id": "20260218_122802_8r3ebz", "status": "passed", "status_reason": "deterministic_output_no_critical_issues", "iterations": 1, "final_validation_confidence": 0, "last_validation_summary": {"consensus": "failed", "passed": false, "critical_count": 0, "issues_count": 0}}}
{"timestamp": "2026-02-19T06:01:22.877055", "event_type": "goal_started", "data": {"goal_id": "20260219_080122_knyew9", "goal": "\n🎯 UKRAINE ENTERPRISE SERVER SEARCH - MULTI-MODEL AI TASK\n========================================================\n\nOBJECTIVE: Find REAL Ukrainian enterprise server offers using Deepseek V3 AI model via OpenRouter.\n\nSEARCH PARAMETERS:\n- Budget: 30,000 - 55,000 UAH\n- Hardware: HP DL380 / Dell PowerEdge R730/R740\n- CPU: 2× Intel Xeon E5 (24-28 cores minimum)\n- RAM: 128-256GB DDR4 ECC\n- Condition: Refurbished / Used-Excellent\n\nPLATFORMS TO SEARCH:\n1. https
{"timestamp": "2026-02-19T06:01:22.891448", "event_type": "plan_selected", "data": {"goal_id": "20260219_080122_knyew9", "iteration": 1, "decision": {"decision": "approved", "consensus": "unanimous", "approval_ratio": 1.0, "avg_confidence": 70.0}, "constraints": {}}}
{"timestamp": "2026-02-19T06:01:59.198166", "event_type": "execution_done", "data": {"goal_id": "20260219_080122_knyew9", "iteration": 1, "execution_status": "success", "execution_time_ms": null}}
{"timestamp": "2026-02-19T06:01:59.203504", "event_type": "validation_done", "data": {"goal_id": "20260219_080122_knyew9", "iteration": 1, "validation_passed": false, "consensus_type": "failed", "confidence": 0, "critical_issues": 0, "total_issues": 0}}
{"timestamp": "2026-02-19T06:01:59.205941", "event_type": "goal_completed", "data": {"goal_id": "20260219_080122_knyew9", "status": "passed", "status_reason": "deterministic_output_no_critical_issues", "iterations": 1, "final_validation_confidence": 0, "last_validation_summary": {"consensus": "failed", "passed": false, "critical_count": 0, "issues_count": 0}}}
```

## f) EXECUTION_DONE TIMELINE

### execution_done és terminal események napi bontásban

| Nap | execution_done | validation_done | goal_completed | goal_failed |
|-----|:--------------:|:---------------:|:--------------:|:-----------:|
| 2026-01-14 | 11 | 11 | 2 | 1 |
| 2026-01-15 | 20 | 20 | 7 | 1 |
| 2026-01-16 | 25 | 25 | 25 | 0 |
| 2026-02-18 | 2 | 2 | 2 | 0 |
| 2026-02-19 | 1 | 1 | 1 | 0 |

### Mind a 59 execution_done rekord — párosítva goal_started és terminal eseménnyel

| # | Nap | goal_id | started_ts | exec_ts | terminal_ts | terminal | duration_s | iter | status |
|---|-----|---------|-----------|---------|-------------|----------|:----------:|:----:|--------|
| 1 | 2026-01-14 | 20260115_001924_tavfd7 | 2026-01-14T22:19:24 | 2026-01-14T22:19:50 | — | — | 26.2 | 1 | success |
| 2 | 2026-01-14 | 20260115_002049_1lczll | 2026-01-14T22:20:49 | 2026-01-14T22:21:06 | 2026-01-14T22:22:27 | completed | 17.2 | 1 | success |
| 3 | 2026-01-14 | 20260115_002049_1lczll | 2026-01-14T22:20:49 | 2026-01-14T22:21:27 | 2026-01-14T22:22:27 | completed | 38.4 | 2 | success |
| 4 | 2026-01-14 | 20260115_002049_1lczll | 2026-01-14T22:20:49 | 2026-01-14T22:21:47 | 2026-01-14T22:22:27 | completed | 58.3 | 3 | success |
| 5 | 2026-01-14 | 20260115_002049_1lczll | 2026-01-14T22:20:49 | 2026-01-14T22:22:06 | 2026-01-14T22:22:27 | completed | 77.2 | 4 | success |
| 6 | 2026-01-14 | 20260115_002049_1lczll | 2026-01-14T22:20:49 | 2026-01-14T22:22:27 | 2026-01-14T22:22:27 | completed | 98.4 | 5 | success |
| 7 | 2026-01-14 | 20260115_002917_0kulvq | 2026-01-14T22:29:17 | 2026-01-14T22:29:34 | 2026-01-14T22:30:50 | completed | 17.2 | 1 | success |
| 8 | 2026-01-14 | 20260115_002917_0kulvq | 2026-01-14T22:29:17 | 2026-01-14T22:29:52 | 2026-01-14T22:30:50 | completed | 34.9 | 2 | success |
| 9 | 2026-01-14 | 20260115_002917_0kulvq | 2026-01-14T22:29:17 | 2026-01-14T22:30:09 | 2026-01-14T22:30:50 | completed | 52.8 | 3 | success |
| 10 | 2026-01-14 | 20260115_002917_0kulvq | 2026-01-14T22:29:17 | 2026-01-14T22:30:27 | 2026-01-14T22:30:50 | completed | 70.6 | 4 | success |
| 11 | 2026-01-14 | 20260115_002917_0kulvq | 2026-01-14T22:29:17 | 2026-01-14T22:30:50 | 2026-01-14T22:30:50 | completed | 93.7 | 5 | success |
| 12 | 2026-01-15 | 20260115_075059_s4qaq7 | 2026-01-15T05:50:59 | 2026-01-15T05:51:20 | 2026-01-15T05:52:42 | completed | 20.5 | 1 | success |
| 13 | 2026-01-15 | 20260115_075059_s4qaq7 | 2026-01-15T05:50:59 | 2026-01-15T05:51:42 | 2026-01-15T05:52:42 | completed | 42.9 | 2 | success |
| 14 | 2026-01-15 | 20260115_075059_s4qaq7 | 2026-01-15T05:50:59 | 2026-01-15T05:52:02 | 2026-01-15T05:52:42 | completed | 62.9 | 3 | success |
| 15 | 2026-01-15 | 20260115_075059_s4qaq7 | 2026-01-15T05:50:59 | 2026-01-15T05:52:19 | 2026-01-15T05:52:42 | completed | 79.7 | 4 | success |
| 16 | 2026-01-15 | 20260115_075059_s4qaq7 | 2026-01-15T05:50:59 | 2026-01-15T05:52:42 | 2026-01-15T05:52:42 | completed | 102.2 | 5 | success |
| 17 | 2026-01-15 | 20260115_075333_4tmhue | 2026-01-15T05:53:33 | 2026-01-15T05:53:56 | 2026-01-15T05:55:23 | completed | 23.7 | 1 | success |
| 18 | 2026-01-15 | 20260115_075333_4tmhue | 2026-01-15T05:53:33 | 2026-01-15T05:54:16 | 2026-01-15T05:55:23 | completed | 43.0 | 2 | success |
| 19 | 2026-01-15 | 20260115_075333_4tmhue | 2026-01-15T05:53:33 | 2026-01-15T05:54:41 | 2026-01-15T05:55:23 | completed | 68.1 | 3 | success |
| 20 | 2026-01-15 | 20260115_075333_4tmhue | 2026-01-15T05:53:33 | 2026-01-15T05:55:04 | 2026-01-15T05:55:23 | completed | 91.0 | 4 | success |
| 21 | 2026-01-15 | 20260115_075333_4tmhue | 2026-01-15T05:53:33 | 2026-01-15T05:55:23 | 2026-01-15T05:55:23 | completed | 110.7 | 5 | success |
| 22 | 2026-01-15 | 20260115_075550_a2mmjv | 2026-01-15T05:55:50 | 2026-01-15T05:56:17 | — | — | 27.7 | 1 | success |
| 23 | 2026-01-15 | 20260115_075550_a2mmjv | 2026-01-15T05:55:50 | 2026-01-15T05:56:42 | — | — | 51.9 | 2 | success |
| 24 | 2026-01-15 | 20260115_075550_a2mmjv | 2026-01-15T05:55:50 | 2026-01-15T05:57:06 | — | — | 76.7 | 3 | success |
| 25 | 2026-01-15 | 20260115_075550_a2mmjv | 2026-01-15T05:55:50 | 2026-01-15T05:57:28 | — | — | 98.1 | 4 | success |
| 26 | 2026-01-15 | 20260115_083559_1rxwj7 | 2026-01-15T06:35:59 | 2026-01-15T06:36:27 | 2026-01-15T06:36:27 | failed | 27.5 | 1 | success |
| 27 | 2026-01-15 | 20260115_083708_fxm2n3 | 2026-01-15T06:37:08 | 2026-01-15T06:37:38 | 2026-01-15T06:37:38 | completed | 29.6 | 1 | success |
| 28 | 2026-01-15 | 20260115_083826_a4zzct | 2026-01-15T06:38:26 | 2026-01-15T06:38:52 | 2026-01-15T06:38:52 | completed | 26.2 | 1 | success |
| 29 | 2026-01-15 | 20260115_084029_xdgsrv | 2026-01-15T06:40:29 | 2026-01-15T06:40:53 | 2026-01-15T06:40:53 | completed | 24.0 | 1 | success |
| 30 | 2026-01-15 | 20260115_085142_1dcpnl | 2026-01-15T06:51:42 | 2026-01-15T06:52:02 | 2026-01-15T06:52:02 | completed | 20.0 | 1 | success |
| 31 | 2026-01-15 | 20260115_090010_d5iw1s | 2026-01-15T07:00:10 | 2026-01-15T07:00:35 | 2026-01-15T07:00:35 | completed | 24.5 | 1 | success |
| 32 | 2026-01-16 | 20260116_195116_rbf7g6 | 2026-01-16T17:51:16 | 2026-01-16T17:51:43 | 2026-01-16T17:51:43 | completed | 27.7 | 1 | success |
| 33 | 2026-01-16 | 20260116_200949_jl04om | 2026-01-16T18:09:49 | 2026-01-16T18:10:19 | 2026-01-16T18:10:19 | completed | 29.8 | 1 | success |
| 34 | 2026-01-16 | 20260116_201058_gkog2y | 2026-01-16T18:10:58 | 2026-01-16T18:11:24 | 2026-01-16T18:11:24 | completed | 25.9 | 1 | success |
| 35 | 2026-01-16 | 20260116_201201_jijb9o | 2026-01-16T18:12:01 | 2026-01-16T18:12:27 | 2026-01-16T18:12:27 | completed | 26.1 | 1 | success |
| 36 | 2026-01-16 | 20260116_201403_lis86x | 2026-01-16T18:14:03 | 2026-01-16T18:14:33 | 2026-01-16T18:14:33 | completed | 30.2 | 1 | success |
| 37 | 2026-01-16 | 20260116_201433_9qefq0 | 2026-01-16T18:14:33 | 2026-01-16T18:14:58 | 2026-01-16T18:14:58 | completed | 25.3 | 1 | success |
| 38 | 2026-01-16 | 20260116_201747_tm4j9c | 2026-01-16T18:17:47 | 2026-01-16T18:18:14 | 2026-01-16T18:18:14 | completed | 26.8 | 1 | success |
| 39 | 2026-01-16 | 20260116_201852_kleud2 | 2026-01-16T18:18:52 | 2026-01-16T18:19:13 | 2026-01-16T18:19:13 | completed | 21.4 | 1 | success |
| 40 | 2026-01-16 | 20260116_202607_z22csk | 2026-01-16T18:26:07 | 2026-01-16T18:26:36 | 2026-01-16T18:26:36 | completed | 28.3 | 1 | success |
| 41 | 2026-01-16 | 20260116_202705_zt513z | 2026-01-16T18:27:05 | 2026-01-16T18:27:29 | 2026-01-16T18:27:29 | completed | 24.4 | 1 | success |
| 42 | 2026-01-16 | 20260116_202749_2qbuob | 2026-01-16T18:27:49 | 2026-01-16T18:28:14 | 2026-01-16T18:28:14 | completed | 25.2 | 1 | success |
| 43 | 2026-01-16 | 20260116_205739_7zjwno | 2026-01-16T18:57:39 | 2026-01-16T18:57:58 | 2026-01-16T18:57:58 | completed | 19.4 | 1 | success |
| 44 | 2026-01-16 | 20260116_205758_2jnuxc | 2026-01-16T18:57:58 | 2026-01-16T18:59:27 | 2026-01-16T18:59:27 | completed | 88.8 | 1 | success |
| 45 | 2026-01-16 | 20260116_205927_1bwy1r | 2026-01-16T18:59:27 | 2026-01-16T18:59:48 | 2026-01-16T18:59:48 | completed | 21.0 | 1 | success |
| 46 | 2026-01-16 | 20260116_210410_x75a7p | 2026-01-16T19:04:10 | 2026-01-16T19:04:33 | 2026-01-16T19:04:33 | completed | 23.7 | 1 | success |
| 47 | 2026-01-16 | 20260116_210433_bqneu6 | 2026-01-16T19:04:33 | 2026-01-16T19:06:04 | 2026-01-16T19:06:04 | completed | 90.3 | 1 | success |
| 48 | 2026-01-16 | 20260116_210604_bdluxu | 2026-01-16T19:06:04 | 2026-01-16T19:06:34 | 2026-01-16T19:06:34 | completed | 30.4 | 1 | success |
| 49 | 2026-01-16 | 20260116_210702_eb3bzu | 2026-01-16T19:07:02 | 2026-01-16T19:07:25 | 2026-01-16T19:07:25 | completed | 23.4 | 1 | success |
| 50 | 2026-01-16 | 20260116_210725_oq9lu3 | 2026-01-16T19:07:25 | 2026-01-16T19:08:56 | 2026-01-16T19:08:56 | completed | 90.4 | 1 | success |
| 51 | 2026-01-16 | 20260116_210856_f3g282 | 2026-01-16T19:08:56 | 2026-01-16T19:09:25 | 2026-01-16T19:09:25 | completed | 29.5 | 1 | success |
| 52 | 2026-01-16 | 20260116_212156_02p8fh | 2026-01-16T19:21:56 | 2026-01-16T19:22:21 | 2026-01-16T19:22:21 | completed | 24.3 | 1 | success |
| 53 | 2026-01-16 | 20260116_212221_hihh9r | 2026-01-16T19:22:21 | 2026-01-16T19:23:48 | 2026-01-16T19:23:48 | completed | 87.2 | 1 | success |
| 54 | 2026-01-16 | 20260116_212348_6ufgxm | 2026-01-16T19:23:48 | 2026-01-16T19:24:16 | 2026-01-16T19:24:16 | completed | 28.0 | 1 | success |
| 55 | 2026-01-16 | 20260116_215359_j0zyv2 | 2026-01-16T19:53:59 | 2026-01-16T19:54:26 | 2026-01-16T19:54:26 | completed | 27.0 | 1 | success |
| 56 | 2026-01-16 | 20260116_215601_9n63c7 | 2026-01-16T19:56:01 | 2026-01-16T19:56:25 | 2026-01-16T19:56:25 | completed | 24.5 | 1 | success |
| 57 | 2026-02-18 | 20260218_122512_4t14y7 | 2026-02-18T10:25:12 | 2026-02-18T10:25:46 | 2026-02-18T10:25:46 | completed | 34.3 | 1 | success |
| 58 | 2026-02-18 | 20260218_122802_8r3ebz | 2026-02-18T10:28:02 | 2026-02-18T10:28:24 | 2026-02-18T10:28:24 | completed | 22.0 | 1 | success |
| 59 | 2026-02-19 | 20260219_080122_knyew9 | 2026-02-19T06:01:22 | 2026-02-19T06:01:59 | 2026-02-19T06:01:59 | completed | 36.3 | 1 | success |

### Incidens-nap (2026-01-14) plan_selected mintája (20 véletlen goal_id)

> Összes plan_selected ezen a napon: 201,802

| goal_id | execution_done? | validation_done? | goal_completed? | goal_failed? |
|---------|:--------------:|:----------------:|:---------------:|:------------:|
| 20260115_001707_7ec5e0 | ❌ | ❌ | ❌ | ❌ |
| 20260114_234638_uthms1 | ❌ | ❌ | ❌ | ❌ |
| 20260115_001610_m861iz | ❌ | ❌ | ❌ | ❌ |
| 20260115_001457_sylhzn | ❌ | ❌ | ❌ | ❌ |
| 20260114_234702_copycq | ❌ | ❌ | ❌ | ❌ |
| 20260114_235647_qfq96t | ❌ | ❌ | ❌ | ❌ |
| 20260114_235636_eh7yvx | ❌ | ❌ | ❌ | ❌ |
| 20260114_235908_v5mkj7 | ❌ | ❌ | ❌ | ❌ |
| 20260115_001524_g7zecm | ❌ | ❌ | ❌ | ❌ |
| 20260114_235938_pqz1j6 | ❌ | ❌ | ❌ | ❌ |
| 20260115_001720_ry7578 | ❌ | ❌ | ❌ | ❌ |
| 20260115_001459_r7wrma | ❌ | ❌ | ❌ | ❌ |
| 20260114_235905_j28wns | ❌ | ❌ | ❌ | ❌ |
| 20260115_001503_cjerj2 | ❌ | ❌ | ❌ | ❌ |
| 20260114_235634_vnppth | ❌ | ❌ | ❌ | ❌ |
| 20260115_001518_8ekpqs | ❌ | ❌ | ❌ | ❌ |
| 20260114_234716_52eg68 | ❌ | ❌ | ❌ | ❌ |
| 20260115_001610_d46tzs | ❌ | ❌ | ❌ | ❌ |
| 20260115_001552_z3gg4u | ❌ | ❌ | ❌ | ❌ |
| 20260115_001659_jjoqgb | ❌ | ❌ | ❌ | ❌ |

**Összesítve a 20 mintából:**
- execution_done-ig eljutott: **0** (0.0%)
- validation_done-ig: **0**
- goal_completed: **0**
- goal_failed: **0**

### Konklúzió

```
execution_done az incidens napján (2026-01-14) : 11
execution_done az incidens UTÁN                     : 48

▶ Az incidens-napon 11 goal eljutott execution-ig.
  Az incidens részleges volt — egyes goal-ok végrehajtódtak.

▶ Az incidens UTÁN indított goal-ok normálisan futottak le (execution_done: 48).
  A pipeline önmagában helyes — a hiba lokalizált az incidens-napra.
```

---
*Riport generálva: `witness/evidence_diagnostic.py` — csak olvasás, sem `meta_evidence.jsonl`, sem `self_state.json` nem módosult.*