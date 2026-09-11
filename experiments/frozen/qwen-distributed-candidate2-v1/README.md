# Frozen Qwen study v1 recorder

These are byte-identical source snapshots used by the 2026-09-09 candidate-2
Qwen Code cohort, preserved before correcting the observed HTTP shutdown race.
They are historical evidence, not the recommended recorder for new studies.

The `.txt` suffix prevents accidental Python import or test discovery. The base
fixture, checker and shared recorder dependencies come from source commit
`a2af59d0d7201aa53cc25252b7fa3f3ed079ebc6`. Module hashes are recorded in each frozen
trial plan and the study's public measurements ledger. No native profiles,
credentials, model transcripts or installed binary artifacts are included here.

To audit the original recorder, use these snapshots in a separate disposable
checkout at that base commit, under their original `experiments/` filenames.
Do not overwrite an active development checkout or run historical replay against
workers that are still executing. Sequencing amendments changed only advancement
between projects; they did not change the frozen worker adapter or task inputs.

Six source snapshots are preserved: the adapter, study launcher, v3 sequencing
controller, native-cancellation classifier, analyzer and v1 public exporter.
Sequencing controller versions 1–3 were documented between-project amendments;
the v3 snapshot is the final historical advancement policy, not a claim that it
existed before B1. The public ledger records their exact source identities.
Current executable v2 modules are for new studies only.
