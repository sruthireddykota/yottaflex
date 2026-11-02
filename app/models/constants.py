from enum import Enum


class AssetStatus(str, Enum):
    AVAILABLE: str = "available"
    IN_TRANSIT: str = "in_transit"
    WITH_CUSTOMER: str = "with_customer"
    DAMAGED: str = "damaged"
    REPAIR: str = "repair"
    LOST: str = "lost"


class AssetCategory(str, Enum):
    PALLET: str = "pallet"
    TOTE: str = "tote"
    CRATE: str = "crate"
    EQUIPMENT: str = "equipment"


class ShipmentStatus(str, Enum):
    PLANNED: str = "planned"
    DISPATCHED: str = "dispatched"
    DELIVERED: str = "delivered"
    RETURNED: str = "returned"


class CustodyEventType(str, Enum):
    DISPATCH: str = "dispatch"
    HANDOFF: str = "handoff"
    RECEIPT: str = "receipt"
    RETURN: str = "return"
    LOSS_DECLARED: str = "loss_declared"


class ReturnStatus(str, Enum):
    REQUESTED: str = "requested"
    IN_TRANSIT: str = "in_transit"
    RECEIVED: str = "received"
    CLOSED: str = "closed"


class InspectionResult(str, Enum):
    PASS: str = "pass"
    DAMAGE: str = "damage"
    MISSING: str = "missing"


class RepairStatus(str, Enum):
    OPEN: str = "open"
    CLOSED: str = "closed"


class LedgerType(str, Enum):
    CHARGE: str = "charge"
    REFUND: str = "refund"


class IssueType(str, Enum):
    SIMULTANEOUS_LOCATIONS: str = "simultaneous_locations"
    RETURN_BEFORE_DISPATCH: str = "return_before_dispatch"
    DEPOSIT_REFUNDED_TWICE: str = "deposit_refunded_twice"
    REPAIR_WITHOUT_INSPECTION: str = "repair_without_inspection"
    CUSTODY_MISSING_ACTOR: str = "custody_missing_actor"
