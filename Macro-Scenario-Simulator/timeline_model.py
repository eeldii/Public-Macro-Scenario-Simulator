"""Quarterly scenario snapshots and explicit hypothetical compounding."""
import re
from model import FACTORS, estimate, validate_shocks

MODES=('Scenario effects (%)','Hypothetical compounded index')

def quarter_index(value, *, allow_baseline=False):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-Q[1-4]',value):
        raise ValueError('Use a quarter such as 2026-Q4.')
    year=int(value[:4])
    if not (1899 if allow_baseline else 1900)<=year<=2200:raise ValueError('Year must be between 1900 and 2200.')
    return year*4+int(value[-1])-1

def quarter_label(index):return f'{index//4}-Q{index%4+1}'

def validate_timeline(points):
    if not isinstance(points,list) or len(points)>80:raise ValueError('A timeline supports at most 80 quarterly scenarios.')
    clean=[];seen=set()
    for point in points:
        if not isinstance(point,dict):raise ValueError('Invalid timeline point.')
        quarter=point.get('quarter');index=quarter_index(quarter)
        if index in seen:raise ValueError('Assign only one scenario per quarter; use Update to replace it.')
        seen.add(index)
        name=point.get('name')
        if not isinstance(name,str) or not 1<=len(name.strip())<=80:raise ValueError('Timeline names must contain 1–80 characters.')
        clean.append(dict(quarter=quarter,name=name.strip(),shocks=validate_shocks(point.get('shocks'))))
    clean.sort(key=lambda p:quarter_index(p['quarter']))
    if clean and quarter_index(clean[-1]['quarter'])-quarter_index(clean[0]['quarter'])>=80:
        raise ValueError('Keep the timeline within 80 consecutive quarters (20 years).')
    return clean

def missing_quarters(points):
    points=validate_timeline(points)
    if not points:return []
    used={quarter_index(p['quarter']) for p in points}
    return [quarter_label(i) for i in range(min(used),max(used)+1) if i not in used]

def fill_gaps(points):
    return validate_timeline([*points,*[dict(quarter=q,name='No shock (explicit gap fill)',shocks=[0]*len(FACTORS)) for q in missing_quarters(points)]])

def series_for(asset, points, mode=MODES[0]):
    points=validate_timeline(points)
    if mode not in MODES:raise ValueError('Unknown timeline view.')
    if not points:return []
    if mode==MODES[1] and missing_quarters(points):
        raise ValueError('Compounding needs every quarter. Assign the missing quarters or explicitly fill gaps with zero change.')
    start=quarter_index(points[0]['quarter'])-1
    series=[(quarter_label(start),100.0 if mode==MODES[1] else 0.0,'Baseline')]
    level=100.0
    for point in points:
        value=estimate(asset,point['shocks'])[1]
        if mode==MODES[1]:
            if value < -100:raise ValueError(f'{asset["name"]}: {point["quarter"]} effect is below −100%; cannot compound a valid long-position price index.')
            level*=1+value/100
            value=level
        series.append((point['quarter'],value,point['name']))
    return series
