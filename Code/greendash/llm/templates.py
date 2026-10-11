# Templates for fallback in case LLM fails or is unavailable

TEMPLATES = {
    "GP01": { # EV Finance
        "ELIGIBLE": "You are eligible for EV Finance. Your transaction history indicates sufficient fuel spend and mileage to benefit from this product.",
        "RECOMMEND": "An EV Finance product is available. Converting to an electric vehicle based on your current fuel spend could reduce carbon emissions.",
        "INELIGIBLE": "Currently, you do not meet the criteria for EV Finance. This may be due to low recorded fuel spend or mileage.",
        "PENDING": "Your EV Finance recommendation is currently pending review.",
        "REJECTED": "Based on your recent transaction profile, an EV Finance product is not recommended at this time.",
        "SOFT_SURFACE": "An EV Finance product is available to review based on your profile.",
        "ABSTAIN": "Insufficient data to evaluate EV Finance at this time.",
        "REVIEW": "Your profile is under review for EV Finance.",
        "RULED_OUT": "EV Finance is not applicable to your profile."
    },
    "GP02": { # Green Home Loan
        "ELIGIBLE": "You are eligible for a Green Home Loan. Your energy consumption profile suggests you could benefit from home efficiency improvements.",
        "RECOMMEND": "A Green Home Loan is available to help reduce your annual gas consumption with better insulation or a new boiler.",
        "INELIGIBLE": "Currently, you do not meet the criteria for a Green Home Loan. Your energy consumption is already highly efficient.",
        "PENDING": "Your Green Home Loan recommendation is pending further data analysis.",
        "REJECTED": "Based on your profile, a Green Home Loan is not recommended at this time.",
        "SOFT_SURFACE": "A Green Home Loan is available to review based on your profile.",
        "ABSTAIN": "Insufficient data to evaluate Green Home Loan at this time.",
        "REVIEW": "Your profile is under review for a Green Home Loan.",
        "RULED_OUT": "A Green Home Loan is not applicable to your profile."
    },
    "GP03": { # Solar Finance
        "ELIGIBLE": "You are eligible for Solar Finance. Your electricity usage indicates you could significantly benefit from solar panels.",
        "RECOMMEND": "Solar Finance is available. Generating your own energy could reduce your annual electricity usage from the grid.",
        "INELIGIBLE": "Currently, you do not meet the criteria for Solar Finance. Your electricity usage may not be high enough to justify the installation cost.",
        "PENDING": "Your Solar Finance recommendation is currently pending.",
        "REJECTED": "Solar Finance is not recommended for your profile at this time.",
        "SOFT_SURFACE": "Solar Finance is available to review based on your profile.",
        "ABSTAIN": "Insufficient data to evaluate Solar Finance at this time.",
        "REVIEW": "Your profile is under review for Solar Finance.",
        "RULED_OUT": "Solar Finance is not applicable to your profile."
    },
    "GP04": { # Paperless Banking
        "ELIGIBLE": "You are eligible to switch to Paperless Banking. Our records show you currently receive paper statements.",
        "RECOMMEND": "Paperless Banking is available. This change reduces paper waste and provides instant access to your statements online.",
        "INELIGIBLE": "You are already using Paperless Banking, or it is not applicable to your account types.",
        "PENDING": "Your Paperless Banking status is pending.",
        "REJECTED": "Paperless Banking is not recommended for your current account structure.",
        "SOFT_SURFACE": "Paperless Banking is available to review based on your profile.",
        "ABSTAIN": "Insufficient data to evaluate Paperless Banking at this time.",
        "REVIEW": "Your profile is under review for Paperless Banking.",
        "RULED_OUT": "Paperless Banking is not applicable to your profile."
    }
}

def get_template(product_id, status, context_data=None):
    """
    Returns the deterministic template for a given product and status.
    Formats the string with context_data if provided.
    """
    if context_data is None:
        context_data = {}
        
    template = TEMPLATES.get(product_id, {}).get(status, "Status information is currently unavailable.")
    
    try:
        return template.format(**context_data)
    except KeyError:
        return template
