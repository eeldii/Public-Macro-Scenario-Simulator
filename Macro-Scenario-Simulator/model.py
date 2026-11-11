"""Offline eight-factor historical model with five explicit local-rate assumptions."""
import copy
import json
import math
from pathlib import Path
from countries import COUNTRIES, EXTRA_MARKETS, asset_name

FACTORS = ('us_rates', 'eu_rates', 'us_inflation', 'eu_inflation', 'us_unemployment', 'eu_unemployment', 'us_gdp', 'eu_gdp')
LABELS = ('US interest rate change (pp)', 'Euro-area interest rate change (pp)', 'US inflation change (pp)', 'Euro-area inflation change (pp)', 'US unemployment change (pp)', 'Euro-area unemployment change (pp)', 'US GDP growth change (pp)', 'Euro-area GDP growth change (pp)')
SHORT_LABELS = ('US rates', 'EU rates', 'US inflation', 'EU inflation', 'US unemployment', 'EU unemployment', 'US GDP', 'EU GDP')
LIMITS = ((-10, 10), (-10, 10), (-15, 15), (-15, 15), (-15, 15), (-15, 15), (-20, 20), (-20, 20))
BASE_FACTORS = FACTORS
FACTORS += ('se_rates','pl_rates','no_rates','ru_rates','gb_rates')
LABELS += tuple(name+' central bank rate change (pp)' for name in EXTRA_MARKETS)
SHORT_LABELS += ('SE rates','PL rates','NO rates','RU rates','UK rates')
LIMITS += ((-20,20),)*5
CHART_ASSETS = ('Broad stocks', 'EUR stocks average', 'US stocks', 'US government bonds', 'EUR Government bonds average', 'US corporate bonds', 'EUR corporate bonds')
PRICE_EFFECT_ASSETS = CHART_ASSETS + tuple(asset_name(country) for country in EXTRA_MARKETS)
CALIBRATION = json.loads((Path(__file__).parent/'data/calibration.json').read_text())
if tuple(CALIBRATION['factors']) != BASE_FACTORS:
    raise ValueError('Calibration factors do not match this app version. Keep the bundled data folder with the app.')
PROVENANCE = {}

def scenario_sensitivities(key, kind):
    """Two-decimal inputs; stock rate and inflation signs follow the user's scenario convention.

    Keep the signed, full-precision empirical fit unchanged in CALIBRATION.
    """
    values = [round(v, 2) for v in CALIBRATION['models'][key]['coefficients']]
    if kind == 'Equity':
        # Inflation signs are a configurable scenario convention, not empirical causation.
        values[2:4] = [abs(v) for v in values[2:4]]
        if key == 'Broad stocks':
            values[2:4] = [round(sum(abs(round(CALIBRATION['models'][region]['coefficients'][i], 2)) for region in ('US stocks', 'EUR stocks average')) / 2, 2) for i in (2, 3)]
        # Domestic rate effects dominate cross-region spillovers by assumption.
        us_home = round(abs(CALIBRATION['models']['US stocks']['coefficients'][0]), 2)
        eu_raw = CALIBRATION['models']['EUR stocks average']['coefficients']
        eu_home = round(max(abs(eu_raw[0]), abs(eu_raw[1])), 2)
        spillover = round(min(us_home, eu_home) / 2, 2)
        if key == 'US stocks':
            values[:2] = [-us_home, -spillover]
        elif key == 'Broad stocks':
            values[:2] = [round(-(us_home + spillover)/2, 2), round(-(eu_home + spillover)/2, 2)]
        else:
            home = round(max(abs(values[0]), abs(values[1])), 2)
            values[:2] = [-round(min(us_home, home)/2, 2), -home]
    if kind in ('Equity', 'Company', 'Bond'):
        direction = -1 if kind == 'Bond' else 1
        values[6:8] = [direction * max(0.01, abs(v)) for v in values[6:8]]
        if key == 'Broad stocks':
            values[6:8] = [round(sum(abs(round(CALIBRATION['models'][region]['coefficients'][i], 2)) for region in ('US stocks', 'EUR stocks average')) / 2, 2) for i in (6, 7)]
    return values + [0]*5

def build_research_defaults():
    result=[]
    for name in CHART_ASSETS:
        kind='Bond' if 'bonds' in name else 'Equity'
        result.append(dict(name=name, kind=kind, sens=scenario_sensitivities(name, kind), duration=0, convexity=0, rate_region='EU' if name.startswith('EUR') else 'US'))
        PROVENANCE[name]=name
    for code,country,*_ in COUNTRIES:
        if code=='US': continue  # Reuse the existing core US stock asset.
        key='country_'+code
        if key not in CALIBRATION['models']: key='EUR stocks average'
        name=asset_name(country)
        result.append(dict(name=name, kind='Equity', sens=scenario_sensitivities(key, 'Equity'), duration=0, convexity=0, rate_region='EU'))
        PROVENANCE[name]=key
        if country in EXTRA_MARKETS:
            asset=result[-1]
            home=abs(asset['sens'][1])
            asset['sens'][1]=-round(home/2,2)
            asset['sens'][8+EXTRA_MARKETS.index(country)]=-home
    return result

RESEARCH_ASSETS = build_research_defaults()
PRESETS = {
    'No shock': [0]*8,
    'US tightening only': [1,0,0,0,0,0,0,0],
    'Euro-area tightening only': [0,1,0,0,0,0,0,0],
    'Illustrative soft landing': [-1,-1,-1,-1,0.2,0.2,0.5,0.5],
    'Illustrative recession': [-2,-2,-1,-1,3,3,-3,-3],
    'Illustrative stagflation': [2,2,3,3,2,2,-2,-2],
    'Illustrative expansion': [0.5,0.5,0.5,0.5,-1,-1,2,2],
}

PRESETS = {name: values+[0]*5 for name,values in PRESETS.items()}
for i, country in enumerate(EXTRA_MARKETS):
    values=[0]*len(FACTORS); values[8+i]=1
    PRESETS[country+' tightening only']=values

def number(value, label='Value'):
    try: result=float(value)
    except (TypeError,ValueError): raise ValueError(f'{label} must be a number.') from None
    if not math.isfinite(result): raise ValueError(f'{label} must be finite.')
    return result

def validate_shocks(values):
    if not isinstance(values,(list,tuple)) or len(values)!=len(FACTORS):
        raise ValueError('A scenario needs exactly thirteen shocks.')
    result=[]
    for value,label,(low,high) in zip(values,LABELS,LIMITS):
        value=number(value,label)
        if not low<=value<=high: raise ValueError(f'{label} must be between {low} and {high}.')
        result.append(value)
    return result

def validate_asset(asset):
    if not isinstance(asset,dict): raise ValueError('Invalid asset record.')
    name=str(asset.get('name','')).strip()
    if not name or len(name)>80: raise ValueError('Asset name must contain 1–80 characters.')
    kind=asset.get('kind')
    if kind not in ('Equity','Bond','Company'): raise ValueError('Asset type must be Equity, Bond, or Company.')
    sens=asset.get('sens')
    if not isinstance(sens,list) or len(sens)!=len(FACTORS): raise ValueError('Each asset needs thirteen sensitivities.')
    sens=[number(v,'Sensitivity') for v in sens]
    if any(abs(v)>100 for v in sens): raise ValueError('Sensitivities must be between −100 and 100.')
    sens=[round(v, 2) for v in sens]
    duration=number(asset.get('duration',0),'Duration'); convexity=number(asset.get('convexity',0),'Convexity')
    if not 0<=duration<=50 or not 0<=convexity<=3000: raise ValueError('Duration must be 0–50; convexity must be 0–3000.')
    region=asset.get('rate_region','US')
    if region not in ('US','EU'): raise ValueError('Bond rate region must be US or EU.')
    return dict(name=name,kind=kind,sens=sens,duration=duration,convexity=convexity,rate_region=region)

def estimate(asset, shocks):
    """Price increments relative to a zero-change baseline; no regression intercept."""
    asset=validate_asset(asset); shocks=validate_shocks(shocks)
    parts=[s*x for s,x in zip(asset['sens'],shocks)]
    if asset['kind']=='Bond':
        i=0 if asset['rate_region']=='US' else 1
        dy=shocks[i]/100
        parts[i]+=100*(-asset['duration']*dy+0.5*asset['convexity']*dy*dy)
    return parts,sum(parts)

def chart_results(assets, shocks, names=CHART_ASSETS):
    by_name={a['name']:a for a in assets}
    return [(name,estimate(by_name[name],shocks)[1] if name in by_name else None) for name in names]

def default_status(asset):
    """Identify exact scenario defaults; provenance describes any empirical overrides."""
    original=next((a for a in DEFAULT_ASSETS if a['name']==asset['name']),None)
    return original is not None and validate_asset(asset)==original

def validate_session(data):
    if not isinstance(data,dict) or data.get('version') not in (5,6):
        raise ValueError('Session format 5 required. Earlier sessions contain currency factors that were replaced by euro-area unemployment and GDP. Recreate those scenarios using the new inputs.')
    if data['version']==5:
        data=copy.deepcopy(data)
        def extend(values):
            if not isinstance(values,list) or len(values)!=8: raise ValueError('Legacy session needs eight factors.')
            return values+[0]*5
        data['shocks']=extend(data.get('shocks'))
        for asset in data.get('assets',[]): asset['sens']=extend(asset.get('sens'))
        for item in [*data.get('scenarios',[]),*data.get('timeline',[])]: item['shocks']=extend(item.get('shocks'))
        data['version']=6
    assets=data.get('assets')
    if not isinstance(assets,list) or not 1<=len(assets)<=100: raise ValueError('A session must have 1–100 assets.')
    assets=[validate_asset(a) for a in assets]
    if len({a['name'].casefold() for a in assets})!=len(assets): raise ValueError('Asset names must be unique.')
    scenarios=data.get('scenarios',[])
    if not isinstance(scenarios,list) or len(scenarios)>12: raise ValueError('At most 12 comparison scenarios are supported.')
    clean=[]
    for s in scenarios:
        if not isinstance(s,dict) or not isinstance(s.get('name'),str) or not 1<=len(s['name'].strip())<=80: raise ValueError('Invalid comparison name.')
        clean.append(dict(name=s['name'].strip(),shocks=validate_shocks(s.get('shocks'))))
    from timeline_model import validate_timeline, MODES
    from themes import THEMES
    timeline=validate_timeline(data.get('timeline',[]))
    theme=data.get('theme','Forest')
    mode=data.get('timeline_mode',MODES[0])
    if isinstance(theme,str) and theme in ('Light','Dark'): theme='Forest'
    if not isinstance(theme,str) or theme not in THEMES:raise ValueError('Unknown visual theme.')
    if not isinstance(mode,str) or mode not in MODES:raise ValueError('Unknown timeline view.')
    return dict(version=6,assets=assets,shocks=validate_shocks(data.get('shocks')),scenarios=clean,timeline=timeline,theme=theme,timeline_mode=mode)


def load_base_assets(data):
    """Load the public default snapshot without recalibrating its coefficients."""
    if not isinstance(data, dict) or data.get('version') != 1 or tuple(data.get('factors', [])) != FACTORS:
        raise ValueError('Base asset snapshot does not match the app factors.')
    records=data.get('assets')
    if not isinstance(records,list) or not 1<=len(records)<=100:
        raise ValueError('Base asset snapshot must contain 1–100 assets.')
    assets=[validate_asset(a) for a in records]
    if len({a['name'].casefold() for a in assets}) != len(assets):
        raise ValueError('Base asset names must be unique.')
    return assets

BASE_ASSET_SOURCE=json.loads((Path(__file__).parent/'data/base_assets.json').read_text())
DEFAULT_ASSETS=load_base_assets(BASE_ASSET_SOURCE)
