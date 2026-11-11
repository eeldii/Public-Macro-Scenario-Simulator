"""Reproduce the historical research slopes offline from the bundled quarterly input panel.
No application dependency. Run: python3 research/calibrate.py
Use --build-panel after download_sources.py to reconstruct the panel from raw sources.
"""
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
FACTORS = ('us_rates', 'eu_rates', 'us_inflation', 'eu_inflation', 'us_unemployment', 'eu_unemployment', 'us_gdp', 'eu_gdp')
COUNTRY_CODES = ('FI','EE','IE','NL','BE','DE','FR','AT','PT','ES','IT','GR')
BONDS = {
    'US government bonds': ('GS10', 10),
    'EUR Government bonds average': ('IRLTLT01EZM156N', 10),
    'US corporate bonds': ('HQMCB7YR', 7),
    'EUR corporate bonds': ('EU_CORPORATE', 5),
}
TARGETS = ['US stocks', 'EUR stocks average', 'Broad stocks', *BONDS,
           *['country_'+c for c in COUNTRY_CODES]]

def invert(matrix):
    n = len(matrix)
    a = [list(row)+[float(i == j) for j in range(n)] for i,row in enumerate(matrix)]
    for c in range(n):
        pivot = max(range(c,n), key=lambda r: abs(a[r][c]))
        if abs(a[pivot][c]) < 1e-10: raise ValueError('Rank-deficient calibration data')
        a[c], a[pivot] = a[pivot], a[c]
        divisor = a[c][c]; a[c] = [v/divisor for v in a[c]]
        for r in range(n):
            if r != c:
                k = a[r][c]; a[r] = [v-k*w for v,w in zip(a[r],a[c])]
    return [row[n:] for row in a]

def regress(x, y):
    n, p = len(y), len(x[0])
    if n <= p: raise ValueError('Not enough observations')
    inv = invert([[sum(row[i]*row[j] for row in x) for j in range(p)] for i in range(p)])
    xy = [sum(row[j]*v for row,v in zip(x,y)) for j in range(p)]
    beta = [sum(a*b for a,b in zip(row,xy)) for row in inv]
    resid = [v-sum(a*b for a,b in zip(row,beta)) for row,v in zip(x,y)]
    # Heteroskedasticity-consistent HC1 covariance; not autocorrelation robust.
    meat = [[sum(e*e*row[i]*row[j] for row,e in zip(x,resid)) for j in range(p)] for i in range(p)]
    se = [math.sqrt(max(0, n/(n-p)*sum(inv[i][k]*meat[k][j]*inv[i][j] for k in range(p) for j in range(p)))) for i in range(p)]
    mean = sum(y)/n
    total = sum((v-mean)**2 for v in y)
    return dict(coefficients=[round(v,6) for v in beta[1:]], intercept=round(beta[0],6),
                hc1_se=[round(v,6) for v in se[1:]], n=n,
                r_squared=round(1-sum(e*e for e in resid)/total,6))

def monthly(series):
    rows = list(csv.reader((ROOT/'research/raw'/f'{series}.csv').read_text(encoding='utf-8-sig').splitlines()))
    grouped = {}
    for row in rows[1:]:
        try:
            date = row[0]
            if len(date)<7 or date[4]!='-': continue
            value = float(row[1])
            if not math.isfinite(value): continue
            grouped.setdefault(date[:7],[]).append(value)
        except (ValueError,IndexError): continue
    return {key:sum(values)/len(values) for key,values in grouped.items()}

def quarterly(series):
    if series in ('GDPC1', 'CLVMNACSCAB1GQEA19'):
        return {(int(k[:4]),(int(k[5:7])-1)//3+1):v for k,v in monthly(series).items()}
    groups = {}
    for date,v in monthly(series).items():
        key=(int(date[:4]),(int(date[5:7])-1)//3+1)
        groups.setdefault(key,[]).append(v)
    return {key:sum(v)/3 for key,v in groups.items() if len(v)==3}

def previous(q, steps=1):
    value=q[0]*4+q[1]-1-steps
    return value//4,value%4+1

def build_panel():
    ids = ['FEDFUNDS','ECBDFR','CPIAUCSL','CP0000EZ19M086NEST','UNRATE','GDPC1','EU_UNEMPLOYMENT','CLVMNACSCAB1GQEA19',
           'SPASTT01USM661N','SPASTT01EZM661N',*[s for s,_ in BONDS.values()],
           *['SPASTT01'+c+'M661N' for c in COUNTRY_CODES]]
    data = {s:quarterly(s) for s in ids}
    def level(s,q): return data[s][q]
    def delta(s,q): return level(s,q)-level(s,previous(q))
    def change(s,q): return 100*(level(s,q)/level(s,previous(q))-1)
    def yoy(s,q): return 100*(level(s,q)/level(s,previous(q,4))-1)
    rows=[]
    for year in range(2000,2026):
        for quarter in range(1,5):
            if year == 2000 and quarter == 1: continue  # Euro-area unemployment starts January 2000.
            if year == 2025 and quarter == 4: continue  # October CPI/jobs missing; no imputation.
            q=year,quarter
            vals=[delta('FEDFUNDS',q),delta('ECBDFR',q),
                  yoy('CPIAUCSL',q)-yoy('CPIAUCSL',previous(q)),
                  yoy('CP0000EZ19M086NEST',q)-yoy('CP0000EZ19M086NEST',previous(q)),
                  delta('UNRATE',q),delta('EU_UNEMPLOYMENT',q),
                  yoy('GDPC1',q)-yoy('GDPC1',previous(q)),
                  yoy('CLVMNACSCAB1GQEA19',q)-yoy('CLVMNACSCAB1GQEA19',previous(q))]
            targets={'US stocks':change('SPASTT01USM661N',q),'EUR stocks average':change('SPASTT01EZM661N',q)}
            targets['Broad stocks']=(targets['US stocks']+targets['EUR stocks average'])/2
            for name,(s,tenor) in BONDS.items():
                targets[name]=100*(((1+level(s,previous(q))/100)/(1+level(s,q)/100))**tenor-1)
            for code in COUNTRY_CODES:
                targets['country_'+code]=change('SPASTT01'+code+'M661N',q)
            rows.append([f'{year}-Q{quarter}',*vals,*[targets[t] for t in TARGETS]])
    with (ROOT/'research/calibration_panel.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['quarter',*FACTORS,*TARGETS]);writer.writerows(rows)

def main():
    if '--build-panel' in sys.argv: build_panel()
    with (ROOT/'research/calibration_panel.csv').open() as f: rows=list(csv.DictReader(f))
    x=[[1,*[float(r[k]) for k in FACTORS]] for r in rows]
    results={}
    for target in TARGETS:
        fit=regress(x,[float(r[target]) for r in rows])
        kept=[i for i,r in enumerate(rows) if not r['quarter'].startswith('2020')]
        fit['excluding_2020']=regress([x[i] for i in kept],[float(rows[i][target]) for i in kept])['coefficients']
        recent=[i for i,r in enumerate(rows) if r['quarter'] >= '2015-Q4']
        fit['recent_10_years']=regress([x[i] for i in recent],[float(rows[i][target]) for i in recent])['coefficients']
        results[target]=fit
    output=dict(version=4, factors=list(FACTORS), start=rows[0]['quarter'],end=rows[-1]['quarter'], excluded_quarters={'2000-Q1':'Eurostat EA21 unemployment starts January 2000; prior quarter unavailable.', '2025-Q4':'October 2025 CPIAUCSL and UNRATE observations are missing; no imputation.'},
                retrieved='2026-11-08',method='Quarterly multivariate OLS with intercept; eight simultaneous factors; HC1 standard errors; intercept omitted from scenario increments.',
                models=results)
    (ROOT/'data/calibration.json').write_text(json.dumps(output,indent=2)+'\n')
    for name in TARGETS[:7]: print(name,results[name]['n'],results[name]['coefficients'],results[name]['r_squared'])

if __name__=='__main__':main()
