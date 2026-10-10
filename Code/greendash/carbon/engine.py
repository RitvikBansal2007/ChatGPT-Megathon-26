def load_factors():
    return {}

def estimate(*args, **kwargs):
    from greendash.contracts import ImpactVerdict, ImpactStatus
    return ImpactVerdict(status=ImpactStatus.NOT_APPLICABLE)

