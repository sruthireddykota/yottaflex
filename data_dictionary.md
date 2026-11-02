# Data dictionary

All IDs are immutable strings. Dates use ISO-8601 `YYYY-MM-DD`; money is stored as a decimal string in the dataset currency. Every child table keeps its parent ID so joins can be validated without inference.

| Table | Key fields | Required relationships / allowed values |
| --- | --- | --- |
| asset_types | `asset_type_id`, `category`, `deposit_amount`, `return_days` | category: pallet, tote, crate, equipment |
| owners | `owner_id`, `owner_type` | owner_type: supplier, customer |
| locations | `location_id`, `location_type` | location_type: warehouse, customer, repair, transit |
| reusable_assets | `asset_id`, `asset_type_id`, `owner_id`, `status`, `current_location_id` | status: available, in_transit, with_customer, damaged, repair, lost |
| shipments | `shipment_id`, origin/destination, `dispatch_date` | status: planned, dispatched, delivered, returned |
| custody_events | `custody_event_id`, `asset_id`, `shipment_id`, event dates | event_type: dispatch, handoff, receipt, return, loss_declared; actor is optional only in labelled anomaly rows |
| return_authorizations | `return_authorization_id`, `asset_id`, `shipment_id` | status: requested, in_transit, received, closed |
| inspections | `inspection_id`, `asset_id`, `return_authorization_id`, `result` | result: pass, damage, missing |
| repairs | `repair_id`, `asset_id`, `inspection_id`, dates | status: open, closed; closed repairs normally require an inspection |
| deposit_ledger | `ledger_id`, `asset_id`, `return_authorization_id`, `entry_type`, `amount` | entry_type: charge, refund; refunds reconcile to charges |

Cardinality is 1:N from asset type, owner, location, shipment, and reusable asset to their child records. A reusable asset can have many custody events, return authorizations, inspections, repairs, and ledger entries. The asset/shipment relationship is N:M over time and is represented by custody events. Event history is append-only; current location and status are derived snapshots.
