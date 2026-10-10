import os
import json
import time
from greenproof.llm.client import get_client

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

def get_explanation(evidence_pack, canary_token="canary123"):
    prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'explain_v1.txt')
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()
        
    prompt = prompt_template.replace('{PACK_JSON}', json.dumps(evidence_pack, indent=2))
    prompt = prompt.replace('{CANARY_TOKEN}', canary_token)
    
    client = get_client()
    
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )
    
    try:
        usage = response.usage_metadata
        if usage:
            tracker.add_cost(usage.prompt_token_count, usage.candidates_token_count)
        else:
            tracker.add_cost(len(prompt)/4, 100)
    except AttributeError:
        tracker.add_cost(len(prompt)/4, 100) 
        
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        print("Failed to decode JSON from LLM")
        return {"explanation": "Failed to generate explanation.", "metrics_summary": ""}

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
