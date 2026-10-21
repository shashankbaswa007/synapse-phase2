import random
from typing import Dict, Any, List
from datetime import datetime
from synapse_simulator.datagen.models import InvoiceLineItem

class BillingGenerator:
    def __init__(self, rng: random.Random):
        self.rng = rng

    def generate_invoice(self, charges: List[InvoiceLineItem]) -> Dict[str, Any]:
        total = sum(c.total_price for c in charges)
        return {
            "total_amount": total,
            "line_items": [c.model_dump() for c in charges],
            "status": "Draft",
            "generated_at": datetime.now().isoformat()
        }
