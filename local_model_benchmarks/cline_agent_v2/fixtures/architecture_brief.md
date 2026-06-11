# Fictional system: RelayBox

RelayBox consumes worker results through `consume_result(job_id)`:

1. Check emergency stop.
2. Validate `ready.json` schema and job ID.
3. Validate the SHA-256 of `result.md`.
4. Mark the result consumed.
5. Send the content to the verdict engine.

A new asynchronous `TaskAdvisor.analyze(description)` API returns optional
planning metadata. It can time out, raise exceptions, or be unavailable. Its
output must never change checksum validation, consumption, or verdicts.

Feature requirements:

- advisory-only and disabled by default;
- at most two seconds of added latency;
- one localized integration point;
- observable status and latency;
- easy rollback;
- no conversion of `consume_result` into an async public API.

Write an implementation plan only. Do not provide production code. Identify
the exact hook location, sync/async boundary, failure behavior, telemetry,
tests, and rollback mechanism.
