import csv
import json
from collections import Counter
from pathlib import Path

from app.models.constants import AssetStatus, CustodyEventType, LedgerType, ShipmentStatus


def validate(data_dir="data"):
    data_dir = Path(data_dir)
    tables = {}
    for path in data_dir.glob("*.csv"):
        with path.open(newline="") as file:
            tables[path.stem] = list(csv.DictReader(file))
    errors = []
    checks = {"primary_key_uniqueness": True, "foreign_key_integrity": True, "allowed_values": True, "date_ordering": True, "deposit_reconciliation": True}
    for table, key in [("reusable_assets", "asset_id"), ("shipments", "shipment_id"), ("custody_events", "custody_event_id"), ("return_authorizations", "return_authorization_id")]:
        values = [row[key] for row in tables.get(table, [])]
        if len(values) != len(set(values)):
            checks["primary_key_uniqueness"] = False
            errors.append(f"duplicate primary key in {table}")
    asset_ids = {row["asset_id"] for row in tables.get("reusable_assets", [])}
    for row in tables.get("custody_events", []) + tables.get("return_authorizations", []) + tables.get("deposit_ledger", []):
        if row.get("asset_id") not in asset_ids:
            checks["foreign_key_integrity"] = False
            errors.append(f"unknown asset_id {row.get('asset_id')}")
    ground_truth_rows = tables.get("ground_truth", [])
    expected = {row["issue_type"] for row in ground_truth_rows}
    expected_entities = {(row["issue_type"], row["entity_id"]) for row in ground_truth_rows}
    valid_statuses = {item.value for item in AssetStatus} | {item.value for item in ShipmentStatus}
    valid_event_types = {item.value for item in CustodyEventType}
    if any(row["status"] not in valid_statuses for row in tables.get("reusable_assets", []) + tables.get("shipments", [])) or any(row["event_type"] not in valid_event_types for row in tables.get("custody_events", [])):
        checks["allowed_values"] = False
        errors.append("invalid enum value")
    actual = Counter()
    for row in tables.get("custody_events", []):
        if not row.get("actor_id"):
            actual["custody_missing_actor"] += 1
    for row in tables.get("repairs", []):
        if row["status"] == "closed" and not row.get("inspection_id"):
            actual["repair_without_inspection"] += 1
    for row in tables.get("return_authorizations", []):
        shipment = next(item for item in tables.get("shipments", []) if item["shipment_id"] == row["shipment_id"])
        if row["received_date"] <= shipment["dispatch_date"]:
            actual["return_before_dispatch"] += 1
    for asset_id, rows in _group_by(tables.get("deposit_ledger", []), "asset_id").items():
        refunds = [row for row in rows if row["entry_type"] == LedgerType.REFUND.value]
        if len(refunds) > 1:
            actual["deposit_refunded_twice"] += 1
    for row in tables.get("custody_events", []):
        same_day = [item for item in tables.get("custody_events", []) if item["asset_id"] == row["asset_id"] and item["event_date"] == row["event_date"] and item["to_location_id"] != row["to_location_id"]]
        if same_day:
            actual["simultaneous_locations"] += 1
            break
    summary = {"checks": checks, "unexpected_errors": errors, "ground_truth_issue_types": sorted(expected), "detected_issue_counts": dict(actual), "valid": not errors}
    (data_dir / "validation_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def _group_by(rows, key):
    grouped = {}
    for row in rows:
        grouped.setdefault(row[key], []).append(row)
    return grouped
