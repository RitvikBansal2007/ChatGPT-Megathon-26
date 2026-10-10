def check(pack, sentences):
    results = []
    has_violation = False
    for s in sentences:
        results.append({"text": s["text"], "check": "PASS", "violations": []})
    
    return {
        "verdict": "FALLBACK" if has_violation else "PASS",
        "sentences": results
    }
