import csv
import hashlib
import json
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from app.models.constants import AssetCategory, AssetStatus, CustodyEventType, IssueType, LedgerType


TABLES = [
    "asset_types", "owners", "locations", "reusable_assets", "shipments",
    "custody_events", "return_authorizations", "inspections", "repairs", "deposit_ledger",
]


def _write_csv(path, rows):
    rows = list(rows)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def generate(output_dir="data", seed=20261022, assets=100, shipments=50, custody_events=250):
    """Generate a reproducible dataset. Defaults are intentionally starter-sized."""
    rng = random.Random(seed)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    base_day = date(2026, 1, 1)

    asset_types = [
        {"asset_type_id": "AT-000001", "name": "Standard Pallet", "category": AssetCategory.PALLET.value, "deposit_amount": "25.00", "return_days": 30},
        {"asset_type_id": "AT-000002", "name": "Reusable Tote", "category": AssetCategory.TOTE.value, "deposit_amount": "12.50", "return_days": 14},
        {"asset_type_id": "AT-000003", "name": "Heavy Crate", "category": AssetCategory.CRATE.value, "deposit_amount": "40.00", "return_days": 45},
        {"asset_type_id": "AT-000004", "name": "Handling Equipment", "category": AssetCategory.EQUIPMENT.value, "deposit_amount": "100.00", "return_days": 60},
    ]
    owners = [{"owner_id": f"OWN-{i:06d}", "name": name, "owner_type": "supplier" if i == 1 else "customer"} for i, name in enumerate(["YottaFlex Pool", "Northwind Supplier", "Acme Retail", "Contoso DC"], 1)]
    locations = [{"location_id": f"LOC-{i:06d}", "name": name, "location_type": kind} for i, (name, kind) in enumerate([("Bengaluru Pool", "warehouse"), ("Chennai Hub", "warehouse"), ("Hyderabad Customer", "customer"), ("Pune Repair Center", "repair"), ("Mumbai Port", "transit")], 1)]
    assets_rows = []
    for i in range(1, assets + 1):
        asset_type = asset_types[(i - 1) % len(asset_types)]
        status = AssetStatus.AVAILABLE.value
        if i % 31 == 0:
            status = AssetStatus.LOST.value
        elif i % 17 == 0:
            status = AssetStatus.DAMAGED.value
        assets_rows.append({"asset_id": f"ASSET-{i:07d}", "asset_type_id": asset_type["asset_type_id"], "owner_id": "OWN-000001", "serial_number": f"SN-{i:08d}", "status": status, "current_location_id": locations[(i - 1) % len(locations)]["location_id"], "acquired_date": str(base_day - timedelta(days=180 + i))})

    shipments_rows = []
    for i in range(1, shipments + 1):
        dispatch_day = base_day + timedelta(days=i % 120)
        shipments_rows.append({"shipment_id": f"SHP-2026-{i:06d}", "from_location_id": locations[0]["location_id"], "to_location_id": locations[2 + i % 2]["location_id"], "owner_id": "OWN-000001", "status": "delivered" if i % 5 else "dispatched", "dispatch_date": str(dispatch_day), "expected_return_date": str(dispatch_day + timedelta(days=14 + i % 25))})

    events = []
    event_count = max(custody_events, assets * 2)
    for i in range(1, event_count + 1):
        asset = assets_rows[(i - 1) % len(assets_rows)]
        shipment = shipments_rows[(i - 1) % len(shipments_rows)]
        event_day = base_day + timedelta(days=(i * 3) % 240)
        event_type = [CustodyEventType.DISPATCH.value, CustodyEventType.HANDOFF.value, CustodyEventType.RECEIPT.value, CustodyEventType.RETURN.value][i % 4]
        events.append({"custody_event_id": f"CUST-{asset['asset_id']}-{i:06d}", "asset_id": asset["asset_id"], "shipment_id": shipment["shipment_id"], "event_type": event_type, "event_date": str(event_day), "from_location_id": shipment["from_location_id"], "to_location_id": shipment["to_location_id"], "actor_id": "OWN-000002" if i % 19 else "", "issue_type": ""})

    returns = []
    inspections = []
    repairs = []
    ledger = []
    ground_truth = []
    for i, asset in enumerate(assets_rows, 1):
        rma_id = f"RMA-2026-{i:06d}"
        shipment = shipments_rows[(i - 1) % len(shipments_rows)]
        return_day = date.fromisoformat(shipment["expected_return_date"]) + timedelta(days=(i % 20) - 5)
        returns.append({"return_authorization_id": rma_id, "asset_id": asset["asset_id"], "shipment_id": shipment["shipment_id"], "status": "received" if i % 4 else "in_transit", "requested_date": shipment["dispatch_date"], "received_date": str(return_day)})
        if i % 17 != 0 and i != 1:
            inspections.append({"inspection_id": f"INS-2026-{i:06d}", "asset_id": asset["asset_id"], "return_authorization_id": rma_id, "inspection_date": str(return_day), "result": "damage" if asset["status"] == "damaged" else "pass", "notes": "visual inspection"})
        if i % 17 == 0 or i == 1:
            repairs.append({"repair_id": f"REP-2026-{i:06d}", "asset_id": asset["asset_id"], "inspection_id": "", "opened_date": str(return_day), "closed_date": str(return_day + timedelta(days=4)), "status": "closed", "cost": "15.00"})
        amount = next(x["deposit_amount"] for x in asset_types if x["asset_type_id"] == asset["asset_type_id"])
        ledger.append({"ledger_id": f"LED-2026-{i:06d}", "asset_id": asset["asset_id"], "return_authorization_id": rma_id, "entry_type": LedgerType.CHARGE.value, "amount": amount, "entry_date": shipment["dispatch_date"]})
        if i % 3 == 0:
            ledger.append({"ledger_id": f"LED-2026-{i:06d}-R", "asset_id": asset["asset_id"], "return_authorization_id": rma_id, "entry_type": LedgerType.REFUND.value, "amount": amount, "entry_date": str(return_day)})

    def issue(issue_type, entity_id, detail):
        ground_truth.append({"issue_id": f"ISSUE-{len(ground_truth) + 1:06d}", "issue_type": issue_type, "entity_id": entity_id, "expected_decision": "review", "details": detail})

    if assets_rows:
        asset = assets_rows[0]
        events[1]["asset_id"] = asset["asset_id"]
        events[0]["to_location_id"] = locations[1]["location_id"]
        events[1]["event_date"] = events[0]["event_date"]
        issue(IssueType.SIMULTANEOUS_LOCATIONS.value, asset["asset_id"], "Two custody events share the same effective date with different destinations")
    if shipments_rows:
        shipment = shipments_rows[0]
        returns[0]["received_date"] = shipment["dispatch_date"]
        issue(IssueType.RETURN_BEFORE_DISPATCH.value, returns[0]["return_authorization_id"], "Return received on or before dispatch")
    if ledger:
        first_refund = next(row for row in ledger if row["entry_type"] == LedgerType.REFUND.value)
        ledger.append({**first_refund, "ledger_id": first_refund["ledger_id"] + "-DUP"})
        issue(IssueType.DEPOSIT_REFUNDED_TWICE.value, first_refund["asset_id"], "Two refunds exist for one charged deposit")
    if repairs:
        issue(IssueType.REPAIR_WITHOUT_INSPECTION.value, repairs[0]["repair_id"], "Closed repair has no inspection foreign key")
    if events:
        missing_actor = next(row for row in events if not row["actor_id"])
        issue(IssueType.CUSTODY_MISSING_ACTOR.value, missing_actor["custody_event_id"], "Custody event actor is blank")

    tables = {"asset_types": asset_types, "owners": owners, "locations": locations, "reusable_assets": assets_rows, "shipments": shipments_rows, "custody_events": events, "return_authorizations": returns, "inspections": inspections, "repairs": repairs, "deposit_ledger": ledger}
    for name, rows in tables.items():
        _write_csv(output / f"{name}.csv", rows)
        (output / f"{name}.json").write_text(json.dumps(rows, indent=2))
    _write_csv(output / "ground_truth.csv", ground_truth)
    (output / "ground_truth.json").write_text(json.dumps(ground_truth, indent=2))
    _write_sqlite_seed(output / "seed.sql", tables)
    manifest = {"seed": seed, "counts": {name: len(rows) for name, rows in tables.items()}, "ground_truth_count": len(ground_truth), "files": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in output.iterdir() if path.is_file()}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def _write_sqlite_seed(path, tables):
    connection = sqlite3.connect(":memory:")
    with path.open("w") as file:
        for name, rows in tables.items():
            columns = list(rows[0]) if rows else []
            file.write(f"CREATE TABLE {name} ({', '.join(f'{column} TEXT' for column in columns)});\n")
            for row in rows:
                values = ", ".join("'" + str(row[column]).replace("'", "''") + "'" for column in columns)
                file.write(f"INSERT INTO {name} ({', '.join(columns)}) VALUES ({values});\n")
    connection.close()
