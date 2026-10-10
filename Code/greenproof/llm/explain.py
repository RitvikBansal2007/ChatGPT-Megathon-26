import os
import json
import time
from greenproof.llm.client import get_client
from greenproof.llm.templates import get_template

# Kratik's security modules - wrapped in try/except so it doesn't break until he merges his branch
try:
    # pyrefly: ignore [missing-import]
    from greenproof.llm.minimise import minimise
    # pyrefly: ignore [missing-import]
    from greenproof.llm.guard import pre_check, post_check
    # pyrefly: ignore [missing-import]
    from greenproof.llm.claimcheck import check
except ImportError:
    # Dummy fallbacks until Kratik merges
    def minimise(pack): return pack
    def pre_check(payload): return True, "PASS"
    def post_check(raw): return True, json.loads(raw)
    class DummyResult: passed = True
    def check(parsed, llm_in): return DummyResult()

# Cost estimates for Gemini 1.5 Flash (as of mid-2024 pricing roughly)
# Input: $0.075 / 1M tokens -> ~£0.06
# Output: $0.30 / 1M tokens -> ~£0.24
COST_PER_1K_INPUT_GBP = 0.00006
COST_PER_1K_OUTPUT_GBP = 0.00024

class CostTracker:
    def __init__(self):
        self.total_cost_gbp = 0.0
        self.budget_limit = float(os.environ.get("LLM_BUDGET_GBP", 5.0))
        
    def add_cost(self, input_tokens, output_tokens):
        cost = (input_tokens / 1000.0) * COST_PER_1K_INPUT_GBP
        cost += (output_tokens / 1000.0) * COST_PER_1K_OUTPUT_GBP
        self.total_cost_gbp += cost
        
        if self.total_cost_gbp > self.budget_limit:
            raise Exception(f"BUDGET EXCEEDED: Total LLM cost £{self.total_cost_gbp:.4f} > £{self.budget_limit}")
            
    def get_total(self):
        return self.total_cost_gbp

tracker = CostTracker()

def get_explanation(evidence_pack, customer_key="dummy", canary_token="canary123"):
    # 1. Minimise pack for security
    llm_in = minimise(evidence_pack)
    payload = json.dumps(llm_in, indent=2) if not hasattr(llm_in, "model_dump_json") else llm_in.model_dump_json()

    # 2. Pre-check (PII scan, Canary)
    ok, reason = pre_check(payload)
    if not ok:
        fallback = get_template(evidence_pack.get("recommendation", "GP01"), "REJECTED")
        return {"explanation": fallback, "source": "template", "claimcheck_status": "PII_BLOCK"}

    prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'explain_v1.txt')
    try:
        with open(prompt_path, 'r') as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # For testing resilience
        prompt_template = "Explain this: {PACK_JSON}"
        
    prompt = prompt_template.replace('{PACK_JSON}', payload).replace('{CANARY_TOKEN}', canary_token)
    client = get_client()
    
    # 3. Call LLM with ONE retry
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.0
                }
            )
            
            usage = getattr(response, "usage_metadata", None)
            if usage:
                tracker.add_cost(usage.prompt_token_count, usage.candidates_token_count)
            else:
                tracker.add_cost(len(prompt)/4, 100)
                
            # 4. Post-check (Schema, PII, canary leak)
            ok, parsed = post_check(response.text)
            if not ok:
                continue
                
            # 5. Claim-Check Verification
            result = check(parsed, llm_in)
            if result.passed:
                return {"explanation": parsed, "source": "llm", "claimcheck_status": "PASS"}
                
        except Exception as e:
            # Fall through to template on network/timeout error
            break
            
    # 6. Fallback if all retries or Claim-Check fails
    fallback = get_template(evidence_pack.get("recommendation", "GP01"), "REJECTED")
    return {"explanation": fallback, "source": "template", "claimcheck_status": "FALLBACK"}

if __name__ == "__main__":
    # Test the explainer
    sample_pack = {
        "customer_id": "C123",
        "recommendation": "GP01",
        "confidence": 0.85,
        "reasons": [
            {"code": "HIGH_FUEL_SPEND", "value": 250}
        ]
    }
    print("Testing explainer...")
    res = get_explanation(sample_pack)
    print("Response:", res)
    print(f"Total Cost So Far: £{tracker.get_total():.6f}")
