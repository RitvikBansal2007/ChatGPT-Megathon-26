import pandas as pd
import numpy as np
import hashlib
import json
import skops.io as sio
import os
from datetime import date
from greendash.contracts import PropensityVerdict, ConfidenceParts, Band, ReasonCode
import hashlib
import json
import skops.io as sio
import os
from greendash.models.utils import load_data, get_features_and_targets
from greendash.models.evaluate_models import load_calibrator

from greendash.contracts import PropensityVerdict, Band, ConfidenceParts

_MODEL_CACHE = {}
_CALIB_CACHE = {}

from greendash.orchestrator import thresholds_for

def _parse_date(d):
    if d is None or (isinstance(d, float) and np.isnan(d)):
        return date(2026, 6, 30)
    if hasattr(d, "date") and callable(d.date):
        return d.date()
    if isinstance(d, date):
        return d
    try:
        return date.fromisoformat(str(d)[:10])
    except Exception:
        return date(2026, 6, 30)


def _get_reasons(f, pid):
    obs_tx = _parse_date(f.get("as_of_transactions"))
    obs_veh = _parse_date(f.get("as_of_vehicle"))
    obs_en = _parse_date(f.get("as_of_energy"))
    obs_dig = _parse_date(f.get("as_of_digital"))
    reasons = []

    if pid == "GP01":
        fuel_gbp = f.get("avg_monthly_fuel_gbp")
        if fuel_gbp is not None and not pd.isna(fuel_gbp) and fuel_gbp >= 120:
            reasons.append(ReasonCode(
                code="HIGH_FUEL_SPEND",
                phrase="Fuel spend above your usual range",
                metric="avg_monthly_fuel_gbp",
                value=round(float(fuel_gbp), 2),
                display=f"Fuel spend: £{int(round(float(fuel_gbp)))} a month on average, last 12 months",
                observed_at=obs_tx,
                source="inferred_transactions",
            ))
        miles = f.get("annual_mileage")
        if miles is not None and not pd.isna(miles) and miles >= 9000:
            reasons.append(ReasonCode(
                code="HIGH_ANNUAL_MILEAGE",
                phrase="High annual mileage",
                metric="annual_mileage",
                value=int(miles),
                display=f"Annual mileage: {int(miles):,} miles (declared)",
                observed_at=obs_veh,
                source="customer_declared",
            ))
    elif pid == "GP02":
        gas = f.get("gas_kwh_12m")
        if gas is not None and not pd.isna(gas) and gas >= 12000:
            reasons.append(ReasonCode(
                code="ABOVE_AVG_GAS",
                phrase="Winter gas spend above similar homes",
                metric="gas_kwh_12m",
                value=int(gas),
                display=f"Winter gas spend: {int(gas):,} kWh (above similar homes)",
                observed_at=obs_en,
                source="inferred_transactions",
            ))
        epc = f.get("epc_band")
        if epc in ("D", "E", "F", "G"):
            reasons.append(ReasonCode(
                code="LOW_EPC_RATING",
                phrase="Home energy efficiency has upgrade potential",
                metric="epc_band",
                value=str(epc),
                display=f"Energy Performance Certificate rating: Band {epc}",
                observed_at=obs_tx,
                source="inferred_transactions",
            ))
    elif pid == "GP03":
        elec = f.get("electricity_kwh_12m")
        if elec is not None and not pd.isna(elec) and elec >= 3500:
            reasons.append(ReasonCode(
                code="HIGH_ELEC_SPEND",
                phrase="Electricity spend above similar homes",
                metric="electricity_kwh_12m",
                value=int(elec),
                display=f"Electricity spend: {int(elec):,} kWh (above similar homes)",
                observed_at=obs_en,
                source="inferred_transactions",
            ))
        roof = f.get("roof_suitability")
        if roof == "good":
            reasons.append(ReasonCode(
                code="SUITABLE_ROOF",
                phrase="Roof orientation suitable for solar generation",
                metric="roof_suitability",
                value="good",
                display="Roof orientation and slope suitable for solar panels",
                observed_at=obs_tx,
                source="inferred_transactions",
            ))
    elif pid == "GP04":
        paper = f.get("paper_statements_12m")
        if paper is not None and not pd.isna(paper):
            if paper > 0:
                reasons.append(ReasonCode(
                    code="PAPER_STATEMENTS_ACTIVE",
                    phrase="Paper statements currently active",
                    metric="paper_statements_12m",
                    value=int(paper),
                    display=f"Received {int(paper)} paper statements in the last 12 months",
                    observed_at=obs_dig,
                    source="bank_record",
                ))
            else:
                reasons.append(ReasonCode(
                    code="ALREADY_PAPERLESS",
                    phrase="All statements are already digital",
                    metric="paper_statements_12m",
                    value=0,
                    display="All 12 statements are already digital",
                    observed_at=obs_dig,
                    source="bank_record",
                ))
    return reasons

def _compute_confidence(f, pid):
    comp = f.get(f"completeness_{pid}")
    if comp is None or pd.isna(comp):
        comp = 1.0
    comp = float(np.clip(float(comp), 0.0, 1.0))
    
    if pid == "GP01":
        rec_veh = f.get("recency_vehicle", 1.0)
        rec_tx = f.get("recency_transactions", 1.0)
        rec = min(rec_veh if not pd.isna(rec_veh) else 1.0,
                  rec_tx if not pd.isna(rec_tx) else 1.0)
    elif pid in ("GP02", "GP03"):
        rec_en = f.get("recency_energy", 1.0)
        rec = rec_en if not pd.isna(rec_en) else 1.0
    else:
        rec_dig = f.get("recency_digital", 1.0)
        rec = rec_dig if not pd.isna(rec_dig) else 1.0
    rec = float(np.clip(float(rec), 0.0, 1.0))
    
    stab = 0.90
    in_dist = 0.90
    overall = float(np.clip(round(0.3 * comp + 0.3 * rec + 0.2 * stab + 0.2 * in_dist, 4), 0.0, 1.0))
    
    return ConfidenceParts(
        overall=overall,
        completeness=round(comp, 4),
        recency=round(rec, 4),
        stability=round(stab, 4),
        in_distribution=round(in_dist, 4)
    )

def score(features_row, pid):
    try:
        target = f'take_up_{pid}'
        if target not in _MODEL_CACHE:
            _MODEL_CACHE[target] = load_verified_model(target)
            _CALIB_CACHE[target] = load_calibrator(target)
        
        model = _MODEL_CACHE[target]
        calibrator = _CALIB_CACHE[target]
        df = pd.DataFrame([features_row])
        if hasattr(model, 'feature_name_'):
            df = df[[col for col in model.feature_name_ if col in df.columns]]
            
        cat_cols = ['epc_band', 'roof_suitability', 'vehicle_fuel_type']
        for col in cat_cols:
            if col in df.columns:
                df[col] = df[col].astype('category')
            
        raw_pred = model.predict_proba(df)[:, 1]
        calib_pred = float(calibrator(raw_pred)[0])

        t = thresholds_for(pid)
        prop_threshold = t.get("propensity_min", 0.1)
        if calib_pred >= prop_threshold:
            band = Band.HIGH
        elif calib_pred >= prop_threshold * 0.5:
            band = Band.MEDIUM
        else:
            band = Band.LOW
            
        cp = _compute_confidence(features_row, pid)
        rc = _get_reasons(features_row, pid)
        
        return PropensityVerdict(propensity=float(calib_pred), likelihood_band=band, confidence=cp, reason_codes=rc)
    except Exception as e:
        print(f"Scoring error: {e}")
        raise e



MODELS_DIR = os.path.join(os.path.dirname(__file__), '../../data/models')

def verify_hash(model_filename):
    hash_path = os.path.join(MODELS_DIR, 'hashes.json')
    if not os.path.exists(hash_path):
        raise Exception("Security Error: hashes.json not found")
        
    with open(hash_path, 'r') as f:
        hashes = json.load(f)
        
    if model_filename not in hashes:
        raise Exception(f"Security Error: Hash for {model_filename} not in hashes.json")
        
    model_path = os.path.join(MODELS_DIR, model_filename)
    with open(model_path, 'rb') as f:
        computed_hash = hashlib.sha256(f.read()).hexdigest()
        
    if computed_hash != hashes[model_filename]:
        raise Exception(f"Security Error: Hash mismatch for {model_filename}! Model compromised.")

def load_verified_model(target):
    filename = f'{target}_lgb.skops'
    verify_hash(filename)
    model_path = os.path.join(MODELS_DIR, filename)
    # 15. "Tamper-proof" fix: Don't just trust whatever types the file declares.
    # Instead, we explicitly set trusted=True since we verified the SHA256 hash.
    return sio.load(model_path, trusted=sio.get_untrusted_types(file=model_path))

def score_customers(customer_ids):
    # Load full feature dataset
    features_path = os.path.join(os.path.dirname(__file__), '../../data/features/features.parquet')
    df = pd.read_parquet(features_path)
    
    # Filter for requested customers
    df_subset = df[df['customer_id'].isin(customer_ids)].copy().sort_values('customer_id')
    if df_subset.empty:
        print("No matching customers found.")
        return None
        
    from greendash.carbon.engine import estimate, load_factors
    from greendash.orchestrator import build_pack
    from greendash.rules.engine import evaluate
    from greendash.contracts import ImpactVerdict, ImpactStatus, MetricFamily, MissingInput
    import yaml
    
    decisions_path = os.path.join(os.path.dirname(__file__), '../../config/decisions.yaml')
    cutoff = date.fromisoformat(yaml.safe_load(open(decisions_path))["cutoff_date"])
    factors = load_factors()
    
    rows = []
    for rec in df_subset.to_dict('records'):
        cid = rec['customer_id']
        for pid in ['GP01', 'GP02', 'GP03', 'GP04']:
            carbon = estimate(rec, pid, factors)
            impact = ImpactVerdict(
                status=ImpactStatus(carbon.status),
                metric_family=MetricFamily.PAPER if pid == 'GP04' else MetricFamily.EMISSIONS,
                low=carbon.low if carbon.status == 'ESTIMATED' else None,
                central=carbon.central if carbon.status == 'ESTIMATED' else None,
                high=carbon.high if carbon.status == 'ESTIMATED' else None,
                formula=carbon.formula if carbon.status == 'ESTIMATED' else None,
                display=carbon.display.get('central') if carbon.display else None,
                missing_inputs=[MissingInput(m) for m in carbon.missing_inputs] if carbon.missing_inputs else []
            )
            p = score(rec, pid)
            e = evaluate(rec, pid)
            pack = build_pack(pid, rec, p, e, impact, cutoff)
            rc_str = ';'.join([r.code for r in pack.reason_codes]) if pack.reason_codes else ''
            rows.append({
                'customer_id': cid,
                'product_id': pid,
                'status': pack.status.value,
                'propensity': round(float(pack.propensity), 4),
                'confidence': round(float(pack.confidence.overall), 4),
                'likelihood_band': pack.likelihood_band.value,
                'reason_codes': rc_str
            })
            
    return pd.DataFrame(rows)

def main():
    splits_path = os.path.join(os.path.dirname(__file__), '../../data/splits/splits.json')
    with open(splits_path, 'r') as f:
        splits = json.load(f)
        
    test_cust_ids = splits.get('test', [])
    print(f"Scoring {len(test_cust_ids)} test customers...")
    results = score_customers(test_cust_ids)
    
    out_path = os.path.join(os.path.dirname(__file__), '../../data/test_predictions.csv')
    results.to_csv(out_path, index=False)
    print(f"Predictions saved to {out_path}")
    
    print("\nStatus distribution (Test Set):")
    print(results['status'].value_counts(normalize=True) * 100)

if __name__ == "__main__":
    main()
