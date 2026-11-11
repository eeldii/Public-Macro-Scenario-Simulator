"""Human-readable methodology shared by the help and explanation tabs."""
from countries import PROXY_COUNTRIES, asset_name
from model import CALIBRATION, DEFAULT_ASSETS, FACTORS, LABELS, PROVENANCE, default_status

METHOD = '''PUBLIC DEFAULT ASSUMPTIONS

This distribution includes only public historical inputs and illustrative scenario assumptions. Fresh launches use zero shocks and no saved scenarios. All sensitivities are editable. Historical fit coefficients are distinct from scenario conventions.

EXPANDED MAP AND LOCAL RATES

The US map result reuses US stocks. Sweden, Poland, Norway, Russia and United Kingdom are explicit euro-area proxies, NOT country-specific historical regressions. They inherit the adjusted euro-area macro sensitivities. Each has its own central-bank-rate change slider: its default local coefficient is the negative euro-area home-rate magnitude (−4.83% per +1 pp), while its ECB coefficient is halved to −2.42%. This transfer is an illustrative assumption, not a measured local response. All other new local-rate sensitivities default to zero, so no cross-country transmission is claimed. You can edit all coefficients. Local rate cuts reverse their contributions. US/euro-area inflation, unemployment and GDP remain external regional inputs, not local data for these five countries. The research snapshot remains the original eight-factor fit; the five added rates are an assumption overlay and have no regression diagnostics. Russia's proxy does not model market closures, sanctions, capital controls, currency translation or investability. Identical macro shocks can produce identical proxy estimates; only the independently assigned local rates distinguish them by default.

The BIS policy-rate dataset documents separate monetary authorities: https://data.bis.org/topics/CBPOL . No current rates are downloaded at startup. Each slider is a percentage-point CHANGE from your baseline. World boundaries use Natural Earth, bundled offline; zoom and pan to inspect smaller countries.

HISTORICALLY INFORMED SCENARIO DEFAULTS · 2000 Q2–2025 Q3 · 102 QUARTERS

The app uses historically estimated magnitudes, rounded to two decimal places. For stock assets, BOTH the US and euro-area rate sensitivities are made negative as a illustrative scenario assumption: positive rate changes reduce the estimated stock price and negative rate changes increase it, all else equal. This sign override is not a historical finding or a claim of causation. Domestic rate effects are stronger than spillovers by explicit scenario design. The current region-specific scenario rate coefficients are shown in the asset table and in the calculation below. US home magnitude comes from its US-rate estimate; euro home magnitude is the larger absolute rate coefficient in the euro-area fit. Cross-region magnitude is half the smaller home magnitude, rounded to two decimals. Each mapped country likewise uses its larger rate magnitude for its euro-area home effect, with a US spillover capped at half the smaller of that magnitude and the US home magnitude. Broad stocks averages the US/euro-area scenario rate coefficients. These are scenario assumptions, not historical estimates of domestic versus foreign transmission. Both US and euro-area inflation sensitivities are made positive using their absolute fitted magnitudes: +1 pp inflation change adds to stock returns and −1 pp subtracts, all else equal. Broad stocks averages the two adjusted regional inflation sensitivities. This is a illustrative scenario convention, not a historical or causal finding. Negative input means falling inflation relative to the baseline, not necessarily deflation. Other coefficients retain their fitted signs. Bond GDP coefficients are negative by scenario convention; other bond coefficients retain their fitted signs. Custom coefficients remain editable, so you can choose a different direction. The underlying raw research coefficients were fitted by multivariate ordinary least squares (OLS), jointly to eight factors with an intercept. “Historical average” means the best-fitting average linear association in this sample, not an average return divided by a rate change, a universal law or a causal policy response.

For each asset we fit: quarterly price change (%) = intercept + sum(coefficient × factor change) + residual. In a scenario we display only sum(coefficient × your shock): an estimated increment relative to the same model at zero changes. The intercept is omitted so zero shocks give zero incremental effect. This is not a forecast of the full quarter's return. The research snapshot retains six decimal places. Scenario sensitivities are rounded to two decimals before calculation, matching the editor and asset table; this also applies when loading or saving custom sensitivities.

GDP magnitudes that round to zero use a minimum 0.01% per percentage point to preserve the requested direction. GDP scenario convention: both regional GDP-growth sensitivities use positive absolute fitted magnitudes for stocks and negative absolute fitted magnitudes for bonds. Negative GDP-growth changes reverse these contributions. Broad stocks averages the adjusted regional stock magnitudes. Other shocks can offset the GDP contribution. These are configurable assumptions, not causal historical findings; custom coefficients remain editable. Inputs are changes in growth from the baseline, not absolute growth levels.

FACTORS AND UNITS

US rates: change in quarterly-average effective federal funds rate (FEDFUNDS). Euro-area rates: change in quarterly-average ECB deposit facility rate (ECBDFR). Rate changes are percentage points. Cross-region rate slopes are estimated, not forced to zero.

US CPI and euro-area HICP inflation: change, in percentage points, in year-on-year inflation calculated from quarterly-average price indices. US and euro-area unemployment: separate changes in quarterly-average seasonally adjusted unemployment rates. US and euro-area GDP: separate changes in year-on-year real GDP growth, in percentage points. Euro-area unemployment is Eurostat une_rt_m (EA21, total age group, all sexes, percent of active population, seasonally adjusted); euro-area GDP is Eurostat CLVMNACSCAB1GQEA19 via FRED. Euro-area unemployment uses the available 21-country aggregate; GDP and stocks use 19 countries. This composition mismatch is an explicit proxy limitation. Unemployment begins in January 2000, so the first usable quarterly change is 2000 Q2; no earlier value is imputed.

Currency appreciation inputs have been removed. Monthly values are averaged into quarters; daily data are first averaged into months. No interpolation or forward-looking lag is used. Stocks are percentage changes between quarterly-average share-price indices, not quarter-end returns. GDP is already quarterly. Contemporaneous revised data do not simulate information available in real time.

ASSET DEFINITIONS

US stocks: OECD US share-price index. EUR stocks average: OECD euro-area (19 countries) aggregate share-price index, not a simple mean of national indices. Broad stocks: an explicit 50/50 average of those US and euro-area local-market quarterly price changes; it is not a world stock index and has no investor-currency conversion.

Government bonds: historical US and euro-area 10-year yield changes transformed into synthetic fixed-10-year zero-coupon repricing. US corporate bonds: Treasury high-quality (AAA/AA/A) 7-year corporate spot yield, transformed using 7 years. EUR corporate bonds: German non-bank corporate yield proxy from the Bundesbank, transformed using an assumed 5 years. That German proxy is NOT a euro-area investment-grade index. The German series has a documented scope change in May 2020.

The bond calibration target is 100 × [((1 + previous yield/100)/(1 + current yield/100))^assumed years − 1]. These are yield-based price proxies, not observed bond-index returns or historical duration averages. Government par/benchmark yields and the German corporate yield are treated as flat discount yields as a modeling approximation. Coupon income, carry, roll-down, defaults and currency conversion are excluded. To avoid counting rates twice, default extra duration and convexity are zero. An optional custom duration/convexity overlay uses the bond's selected US or EU rate; it is separate from the fitted slopes.

COUNTRIES AND COMPANIES

Twelve country markets have their own OECD share-price regressions using the same eight factors and sample. Latvia and Lithuania use the euro-area aggregate model as an explicit proxy because equivalent country series were unavailable. Their map colours are not country-specific empirical estimates. New user companies start with zero coefficients: no company research is fabricated from a ticker.

INTERPRETING THE RESULTS

A coefficient can have a surprising sign: US rates and stocks sometimes rose together as growth improved. The scenario defaults make both rate contributions negative by assumption, regardless of the signs in the original fit. That does NOT mean a surprise rate hike causes stocks to rise. Bernanke and Kuttner's Federal Reserve event study found approximately +1% equities for a surprise 25 bp cut; its event window and identified surprises are different from these quarterly associations. ECB research similarly distinguishes policy shocks from information about the economy. Do not mix those causal interpretations with this app's coefficients.

The explanation tab shows sample size, fit R², HC1 standard errors and coefficients refitted without 2020 and over the most recent 40 quarters (2015 Q4–2025 Q3). A large change in the latter is a warning about sample sensitivity. HC1 allows heteroskedasticity but not serial correlation; these are diagnostics, not reliable forecast confidence intervals. No out-of-sample performance or causal identification is claimed. Correlated factors and only 102 quarters make coefficients unstable. Large scenario changes extrapolate beyond the historical sample. Estimates below −100% indicate model breakdown; they remain visible.

TIMELINE AND APPEARANCE

Timeline points snapshot thirteen shocks and a name at each assigned quarter. Scenario-effects view compares independent effects against the same zero-change baseline; unassigned gaps are not filled or forecast. Connecting lines are visual guides only. Compounded view starts at index 100 in the preceding quarter and treats each assigned increment as if it were a quarterly price return: next index = previous index × (1 + effect/100). This is an additional hypothetical assumption, not an estimated total-return forecast. All intermediate quarters must be explicitly assigned; you may explicitly fill missing quarters with zero change. Effects below −100% cannot be compounded. Current asset assumptions recalculate every timeline point. Forest is the sole visual theme.

REPRODUCIBILITY AND SOURCES

Research.md documents all series, transformations and proxy limitations. research/calibration_panel.csv contains the fixed transformed input data; research/calibrate.py reproduces the raw regression coefficients offline. All models were refitted after replacing the two currency predictors with euro-area unemployment and GDP; currency slopes were not reused. The scenario layer then rounds them and overrides stock-rate and inflation signs as described above. data/calibration.json stores the fitted results and diagnostics. Sources were retrieved 8 November 2026; the sample ends at the last complete common quarter, 2025 Q3. October 2025 CPI and unemployment observations are missing, so 2025 Q4 is excluded without imputation. This expands the sample from 80 to 102 quarters (27.5%). A longer sample does not guarantee greater accuracy. The app never downloads market data at startup.

OECD Main Economic Indicators via FRED: https://fred.stlouisfed.org/series/SPASTT01USM661N and https://fred.stlouisfed.org/series/SPASTT01EZM661N
Rates: https://fred.stlouisfed.org/series/FEDFUNDS and https://fred.stlouisfed.org/series/ECBDFR
Euro-area GDP: https://fred.stlouisfed.org/series/CLVMNACSCAB1GQEA19
Euro-area unemployment: https://ec.europa.eu/eurostat/databrowser/view/une_rt_m/default/table?lang=en
Bonds: https://fred.stlouisfed.org/series/GS10 , https://fred.stlouisfed.org/series/IRLTLT01EZM156N , https://fred.stlouisfed.org/series/HQMCB7YR
German corporate yield: https://api.statistiken.bundesbank.de/rest/download/BBSIS/M.I.UMR.RD.EUR.X2000.B.A.A.R.A.A._Z._Z.A?format=csv&lang=en
Federal Reserve research: https://www.federalreserve.gov/econres/feds/what-explains-the-stock-market39s-reaction-to-federal-reserve-policy.htm
ECB research: https://www.ecb.europa.eu/press/research-publications/resbull/2018/html/ecb.rb180921.el.html
Map: Natural Earth public-domain country boundaries, bundled for offline use. Background countries have no modeled equity effect; colours represent selected stock markets, not countries' welfare.
'''

DESCRIPTIONS = {
 'Broad stocks':'Synthetic 50/50 blend of US and euro-area local-market price changes, not a global index.',
 'US stocks':'OECD US share prices, local-market price index.',
 'EUR stocks average':'OECD euro-area 19-country share-price aggregate, not a simple country average.',
 'US government bonds':'Synthetic 10-year zero-coupon repricing using US Treasury GS10 yields.',
 'EUR Government bonds average':'Synthetic 10-year zero-coupon repricing using the OECD euro-area 19-country benchmark yield.',
 'US corporate bonds':'Synthetic 7-year zero-coupon repricing using Treasury high-quality corporate spot yields (AAA/AA/A).',
 'EUR corporate bonds':'German non-bank corporate yield proxy with assumed 5-year repricing; not a euro-area corporate return index.',
}

def provenance_text(asset):
    key=PROVENANCE.get(asset['name'])
    if not default_status(asset):
        return 'CUSTOM ASSUMPTIONS: these inputs differ from the public base or have no matched historical model. Do not describe the current coefficients as historical averages.\n'
    if key is None:
        return 'PUBLIC BASE ASSUMPTIONS: illustrative defaults; no matched historical model.\n'
    model=CALIBRATION['models'][key]
    proxy=asset['name'] in tuple(asset_name(c) for c in PROXY_COUNTRIES)
    description=DESCRIPTIONS.get(key,'Country-specific OECD share-price regression.')
    body='PUBLIC BASE ASSUMPTIONS: derived from public research with explicit scenario adjustments. Current values are not the original fitted coefficients.\n'
    body+='Historical reference only: '+description+'\n'
    if proxy: body+='Historical reference uses a regional proxy, not a country-specific fit.\n'
    body+='The diagnostics below show the ORIGINAL SIGNED fits; the current scenario arithmetic follows separately.\n'
    body+=f"Sample {CALIBRATION['start']} to {CALIBRATION['end']}; n={model['n']}; in-sample R²={model['r_squared']:.3f}.\n"
    body+=f"Fitted intercept {model['intercept']:+.3f}% is excluded from scenario increments.\n\n"
    body+='Original research fit (not the adjusted scenario input): slope | HC1 standard error | slope excluding 2020 | recent 10-year slope\n'
    for label,coef,se,alternate,recent in zip(LABELS,model['coefficients'],model['hc1_se'],model['excluding_2020'],model['recent_10_years']):
        body+=f'{label}: {coef:+.4f} | {se:.4f} | {alternate:+.4f} | {recent:+.4f}\n'
    return body
