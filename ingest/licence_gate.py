# ingest/licence_gate.py

ALLOW = frozenset({"OGL-UK-3.0", "CC-BY-4.0", "CC0-1.0"})

def check(src: dict, manually_approved: frozenset = frozenset()) -> bool:
    """
    Gate data source by licence.
    """
    ok = src["licence"] in ALLOW or src["id"] in manually_approved
    decision = "PASS" if ok else "REJECT"
    print(f"{decision} {src['id']} licence={src['licence']}")
    return ok
