import pytest
from greenproof.llm.templates import TEMPLATES, get_template

# Placeholder for the claimcheck if not yet merged
try:
    from greenproof.llm.guard import claimcheck
except ImportError:
    def claimcheck(text):
        # Dummy claimcheck that passes anything without forbidden words
        forbidden = ["guarantee", "100%", "promise"]
        for f in forbidden:
            if f in text.lower():
                return False
        return True

def test_all_templates_pass_claimcheck():
    context = {
        "fuel_spend": "100",
        "gas_kwh": "2000",
        "elec_kwh": "1500"
    }
    
    for product_id, statuses in TEMPLATES.items():
        for status, template_text in statuses.items():
            text = get_template(product_id, status, context)
            
            # Assert that the template passes the claimcheck (must not contain guarantees etc.)
            assert claimcheck(text) is True, f"Template {product_id} {status} failed claimcheck!"
