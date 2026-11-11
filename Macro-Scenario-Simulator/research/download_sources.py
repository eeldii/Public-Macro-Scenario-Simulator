"""Optional developer download; app and calibration reproduction do not require network.
Run this then `python3 research/calibrate.py --build-panel` to refetch/rebuild inputs.
New revisions can change results; the bundled panel preserves the original calibration.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import csv
import io
import json
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from calibrate import COUNTRY_CODES

ROOT=Path(__file__).resolve().parents[1]
SERIES=['FEDFUNDS','ECBDFR','CPIAUCSL','CP0000EZ19M086NEST','UNRATE','GDPC1','CLVMNACSCAB1GQEA19',
        'SPASTT01USM661N','SPASTT01EZM661N','GS10','IRLTLT01EZM156N','HQMCB7YR',
        *['SPASTT01'+c+'M661N' for c in COUNTRY_CODES]]
URLS={s:'https://fred.stlouisfed.org/graph/fredgraph.csv?id='+s for s in SERIES}
URLS['EU_CORPORATE']='https://api.statistiken.bundesbank.de/rest/download/BBSIS/M.I.UMR.RD.EUR.X2000.B.A.A.R.A.A._Z._Z.A?format=csv&lang=en'

URLS['EU_UNEMPLOYMENT']='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?lang=en&geo=EA21&sex=T&age=TOTAL&unit=PC_ACT&s_adj=SA&sinceTimePeriod=1999-01'

def eurostat_csv(data):
    payload=json.loads(data)
    # One series: every non-time dimension must have exactly one selected value.
    if payload['id'][-1] != 'time' or any(size != 1 for size in payload['size'][:-1]):
        raise ValueError('Expected a single monthly Eurostat series')
    dates=payload['dimension']['time']['category']['index']
    values=payload['value']
    out=io.StringIO(); writer=csv.writer(out); writer.writerow(['observation_date','EU_UNEMPLOYMENT'])
    for date,index in sorted(dates.items()):
        value=values.get(str(index)) if isinstance(values,dict) else values[index]
        if value is not None: writer.writerow([date+'-01',value])
    return out.getvalue().encode()

def download(item):
    name,url=item
    # Use the system trust store on macOS when the Python CA bundle is absent.
    context=ssl.create_default_context(cafile='/etc/ssl/cert.pem') if Path('/etc/ssl/cert.pem').exists() else ssl.create_default_context()
    try:
        with urllib.request.urlopen(url,context=context,timeout=40) as response: data=response.read()
    except urllib.error.URLError as exc:
        # macOS curl can use the system keychain when a Python CA bundle is incomplete.
        # Certificate validation stays enabled; other download failures are surfaced.
        if sys.platform != 'darwin' or not isinstance(exc.reason, ssl.SSLCertVerificationError): raise
        data=subprocess.check_output(['/usr/bin/curl','--fail','--silent','--show-error','--location','--max-time','40',url])
    if name == 'EU_UNEMPLOYMENT': data=eurostat_csv(data)
    (ROOT/'research/raw'/f'{name}.csv').write_bytes(data)
    print('Downloaded',name)

if __name__=='__main__':
    (ROOT/'research/raw').mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(download,URLS.items()))
