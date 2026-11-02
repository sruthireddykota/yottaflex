# Reusable Asset Coordination Data Generator

## Project overview

This project generates synthetic logistics data for coordinating reusable pallets, totes, crates, and handling equipment across suppliers, warehouses, carriers, and customers.

It models the complete asset lifecycle:

- Asset types, owners, and locations
- Reusable assets and their current status
- Shipments and custody transfers
- Return authorizations
- Inspections and repairs
- Deposit charges and refunds
- Lost, damaged, delayed, and disputed asset scenarios

The generator creates master data first, then creates dependent records using valid parent IDs. State changes are represented as custody events so that an asset's movement history remains traceable.

## Project structure

```text
yottaflex/
├── app/
│   ├── main.py                 # Command-line entry point
│   ├── models/constants.py     # Domain enums
│   └── services/
│       ├── generator.py        # Deterministic data generation
│       └── validation.py       # Data-quality validation
├── data_dictionary.md          # Fields, relationships, and allowed values
├── Dockerfile
├── requirements.txt
└── tests/
```

The project uses simple `str, Enum` classes for allowed business values, such as asset status, shipment status, custody event type, and issue type.

## Docker setup

Build the image from the repository root:

```bash
docker build -t yottaflex .
```

Generate the starter dataset. The `data` folder on the host is mounted into the container so the generated files remain available locally:

```bash
docker run --rm \
  -v "$PWD/data:/app/data" \
  yottaflex
```

The default Docker command creates 100 reusable assets, 50 shipments, and 250 custody events. The container is a batch data generator, so it exits after generation. This is expected behavior. The `--rm` option removes the stopped container after completion, while the generated files remain in the local `data` directory.

## Validate the generated data

```bash
docker run --rm \
  -v "$PWD/data:/app/data" \
  yottaflex \
  python -m app.main validate --data-dir /app/data
```

Validation checks primary-key uniqueness, foreign-key integrity, allowed enum values, date ordering, deposit reconciliation, and labelled operational exceptions.

## Full-scale generation

```bash
docker run --rm \
  -v "$PWD/data:/app/data" \
  yottaflex \
  python -m app.main generate \
  --output /app/data \
  --seed 20261022 \
  --assets 20000 \
  --shipments 10000 \
  --custody-events 100000
```

The same seed and parameters produce the same row counts and file checksums, demonstrating reproducibility.

## Generated outputs

The `data` directory contains CSV and JSON files for `asset_types`, `owners`, `locations`, `reusable_assets`, `shipments`, `custody_events`, `return_authorizations`, `inspections`, `repairs`, and `deposit_ledger`, plus:

```text
ground_truth.csv/json
seed.sql
manifest.json
validation_summary.json
```

`ground_truth.csv` is separate from the input tables. It records expected decisions for known exception cases and is not mixed into the generated business data.

## Example validation result

The starter dataset generated with seed `20261022` produced:

```json
{
  "checks": {
    "primary_key_uniqueness": true,
    "foreign_key_integrity": true,
    "allowed_values": true,
    "date_ordering": true,
    "deposit_reconciliation": true
  },
  "unexpected_errors": [],
  "ground_truth_issue_types": [
    "custody_missing_actor",
    "deposit_refunded_twice",
    "repair_without_inspection",
    "return_before_dispatch",
    "simultaneous_locations"
  ],
  "valid": true
}
```

The detected issue counts for the starter run were:

```text
custody_missing_actor: 13
repair_without_inspection: 6
return_before_dispatch: 1
deposit_refunded_twice: 1
simultaneous_locations: 1
```

The five rows in `ground_truth.csv` provide one canonical labelled example for each required anomaly type. Counts can be higher for recurring anomalies such as missing actors or repairs without inspections; these are expected exception patterns, not unexpected data corruption. Therefore, `valid: true` means the data passed structural validation while known operational exceptions were preserved for review.

## Ground-truth scenarios

The generator includes these documented edge cases:

1. An asset appears to have two simultaneous locations.
2. A return is processed before dispatch.
3. A deposit is refunded twice.
4. A repair closes without an inspection.
5. A custody event has no actor.

Each case is labelled with an `issue_type`, `entity_id`, `expected_decision`, and explanation in `ground_truth.csv`.

## Testing

```bash
python3 -m unittest discover -v
```

See [data_dictionary.md](data_dictionary.md) for the complete field dictionary, relationships, allowed values, and validation rules.
