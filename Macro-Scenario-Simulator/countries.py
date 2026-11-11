"""Selected markets and label anchors (longitude, latitude). Real borders are in data/."""
EXTRA_MARKETS = ('Sweden','Poland','Norway','Russia','United Kingdom')
PROXY_COUNTRIES = ('Latvia','Lithuania',*EXTRA_MARKETS)
COUNTRIES = [
 ('US','United States',-98,39),('SE','Sweden',16,63),('PL','Poland',19,52),
 ('NO','Norway',9,62),('RU','Russia',90,61),('GB','United Kingdom',-2,54),
 ('FI','Finland',26,64),('EE','Estonia',25.5,58.7),('LV','Latvia',24.5,56.8),
 ('LT','Lithuania',24,55.1),('IE','Ireland',-8,53.3),('NL','Netherlands',5.4,52.3),
 ('BE','Belgium',4.5,50.5),('DE','Germany',10.5,51),('FR','France',2,46.5),
 ('AT','Austria',14,47.6),('PT','Portugal',-8,39.6),('ES','Spain',-3.5,40),
 ('IT','Italy',12.6,42.5),('GR','Greece',23,38.7),
]
def asset_name(country): return 'US stocks' if country=='United States' else country+' stocks'

def effect_color(value):
    if abs(value)<0.005: return '#e3e9ef'
    strength=min(abs(value)/10,1)**0.5
    start=(247,234,236) if value<0 else (226,245,236)
    end=(150,12,35) if value<0 else (0,100,55)
    return '#'+''.join(f'{round(a+(b-a)*strength):02x}' for a,b in zip(start,end))
