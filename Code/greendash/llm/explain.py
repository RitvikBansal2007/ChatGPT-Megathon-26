import os
import json
import time
from greendash.llm.client import get_client
from greendash.llm.templates import get_template

# Security modules - wrapped in try/except so it doesn't break until merged
try:
    # pyrefly: ignore [missing-import]
    from greendash.llm.minimise import minimise
    # pyrefly: ignore [missing-import]
    from greendash.llm.guard import pre_check, post_check
    # pyrefly: ignore [missing-import]
    from greendash.llm.claimcheck import check
except ImportError:
    # Fail-closed safe fallbacks: if security modules fail to load, ALWAYS reject LLM usage.
    def minimise(pack): return pack
    def pre_check(payload): return False, "SECURITY_MODULE_UNAVAILABLE"
    def post_check(raw): return False, {}
    class DummyResult: passed = False
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
        fallback = get_template(evidence_pack.get("opportunity_id", "GP01"), evidence_pack.get("status", "REJECTED"))
        return {"sentences": [{"text": fallback, "fields": [], "check": "TEMPLATE"}], "source": "template", "claimcheck_status": "FALLBACK"}

    prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'explain_v1.txt')
    system_path = os.path.join(os.path.dirname(__file__), 'prompts', 'system_v1.txt')
    try:
        with open(prompt_path, 'r') as f:
            prompt_template = f.read()
        with open(system_path, 'r') as f:
            system_template = f.read()
    except FileNotFoundError:
        # For testing resilience
        prompt_template = "Explain this: {PACK_JSON}"
        system_template = "You are a helpful assistant. Canary: {CANARY}"
        
    system_prompt = system_template.replace('{CANARY}', canary_token)
    prompt = prompt_template.replace('{PACK_JSON}', payload)
    full_prompt = system_prompt + "\n" + prompt
    client = get_client()
    
    # 3. Call LLM with ONE retry
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=full_prompt,
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
                # Need to map the raw parsed JSON list to Sentence objects shape if it isn't already
                if isinstance(parsed, dict) and "sentences" in parsed:
                    sents = parsed["sentences"]
                else:
                    sents = [{"text": str(parsed), "fields": [], "check": "PASS"}]
                return {"sentences": sents, "source": "llm", "claimcheck_status": "PASS"}
                
        except Exception as e:
            # Fall through to template on network/timeout error
            break
            
    # 6. Fallback if all retries or Claim-Check fails
    fallback = get_template(evidence_pack.get("opportunity_id", "GP01"), evidence_pack.get("status", "REJECTED"))
    return {"sentences": [{"text": fallback, "fields": [], "check": "TEMPLATE"}], "source": "template", "claimcheck_status": "FALLBACK"}

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
