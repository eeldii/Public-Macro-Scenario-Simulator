# Research and assumptions

The public default assets are generated from bundled historical estimates plus explicit scenario conventions. They contain no personal workbook edits or saved user sessions. Stock-rate sensitivities are negative with stronger home-region effects. Stock inflation/GDP sensitivities are positive; bond GDP sensitivities are negative. These signs are configurable assumptions, not causal findings. Broad stocks combines the regional reference models. The five added local-rate factors are assumed overlays, not fitted regressors.

## Sample expansion and completeness

The new euro-area unemployment series starts in January 2000, leaving no prior-quarter rate for Q1 2000. That first quarter is excluded without imputation. The public reference contains 102 complete quarters. October 2025 CPIAUCSL and UNRATE observations are missing, so Q4 2025 is excluded. We neither interpolate those months nor substitute two-month quarterly averages. The next 2026 quarter is also incomplete in the euro-area price data. The common sample therefore ends in 2025 Q3. Longer history adds earlier cycles but does not guarantee improved accuracy; definitions and economic regimes change over time.

The snapshot also stores a `recent_10_years` coefficient vector fitted on the most recent 40 quarters (2015 Q4–2025 Q3), alongside the existing excluding-2020 diagnostic. These comparisons show sample dependence; neither is a separate automatically selected model. Scenario rate sign/domestic-effect adjustments remain explicit assumptions layered over the fitted slopes.

## Method

Each asset has a separate ordinary least-squares regression with an intercept and the same eight simultaneous predictors:

`quarterly price change (%) = intercept + β₁ × US rate change + β₂ × EU rate change + β₃ × US inflation change + β₄ × EU inflation change + β₅ × US unemployment change + β₆ × EU unemployment change + β₇ × US GDP-growth change + β₈ × EU GDP-growth change + residual`

The app reports **adjusted scenario coefficient × scenario shocks only**, excluding the intercept. It represents an incremental difference from the fitted model's zero-change baseline; it is not the full fitted quarter's return. No historical drift or investment-income forecast is added. Research coefficients are stored to six decimals. Scenario inputs use two decimals, with negative stock-rate and positive stock-inflation magnitudes; bond GDP signs are negative by convention; other bond signs are unchanged. “Historical averages” here means estimated average linear slopes conditional on the other included factors, not arithmetic averages of return/shock ratios.

Raw daily observations are averaged to months; three monthly observations are averaged to quarters. A quarter missing a month is rejected rather than interpolated. Real GDP is already quarterly. Price-index returns are simple percentage changes between quarterly means, not quarter-end returns. Inflation is year-on-year growth in quarterly-mean CPI/HICP, then differenced from the previous quarter. GDP growth is year-on-year real growth, also differenced from the previous quarter. Rates and unemployment are quarter-to-quarter changes in quarterly means, in percentage points. Lagged observations before 2000 are used solely to construct transformations.

OLS uses all eight factors jointly, with no sign constraints or coefficient clipping. There is no exclusion of recessions or COVID from the defaults. `hc1_se` stores heteroskedasticity-consistent HC1 standard errors. `excluding_2020` refits after removing all four quarters of 2020; it is a diagnostic, not a second default. `recent_10_years` provides the most recent 40-quarter refit. HC1 does not correct serial correlation. R² is in-sample fit, not predictive accuracy. All targets use the same 102 observations.

The reproducible code is [research/calibrate.py](research/calibrate.py), the transformed inputs are [research/calibration_panel.csv](research/calibration_panel.csv), and fitted results are [data/calibration.json](data/calibration.json). Run `python3 research/calibrate.py` to reproduce the coefficient file without internet or third-party packages. Optional `research/download_sources.py` refetches source histories; a subsequent `--build-panel` rebuild can differ because source data are revised. The fixed bundled panel is the original version of the inputs.

## Source ledger

Unless noted, series were retrieved through the Federal Reserve Bank of St. Louis's FRED service. Source identifiers below link to their definitions and underlying publishers. Cite the original publishers as well as FRED when reusing the research inputs. The included panel is transformed research data, not a redistribution of a full market-data history.

| Input | Series / publisher | Use |
|---|---|---|
| US short-term rate | [FEDFUNDS — Federal Reserve](https://fred.stlouisfed.org/series/FEDFUNDS) | Effective federal funds rate |
| Euro-area short-term rate | [ECBDFR — ECB](https://fred.stlouisfed.org/series/ECBDFR) | Deposit facility rate |
| US prices | [CPIAUCSL — BLS](https://fred.stlouisfed.org/series/CPIAUCSL) | Seasonally adjusted all-items CPI |
| Euro-area prices | [CP0000EZ19M086NEST — Eurostat](https://fred.stlouisfed.org/series/CP0000EZ19M086NEST) | All-items HICP, fixed 19-country composition |
| US unemployment | [UNRATE — BLS](https://fred.stlouisfed.org/series/UNRATE) | Seasonally adjusted US unemployment |
| US GDP | [GDPC1 — BEA](https://fred.stlouisfed.org/series/GDPC1) | Seasonally adjusted US real GDP |
| Euro-area unemployment | [une_rt_m — Eurostat](https://ec.europa.eu/eurostat/databrowser/view/une_rt_m/default/table?lang=en) | EA21, TOTAL age, all sexes (T), percent of active population (PC_ACT), seasonally adjusted (SA), monthly |
| Euro-area GDP | [CLVMNACSCAB1GQEA19 — Eurostat via FRED](https://fred.stlouisfed.org/series/CLVMNACSCAB1GQEA19) | EA19, millions of chained 2010 euros, seasonally adjusted, quarterly |
| US equity prices | [SPASTT01USM661N — OECD](https://fred.stlouisfed.org/series/SPASTT01USM661N) | US share-price index |
| Euro-area equity prices | [SPASTT01EZM661N — OECD](https://fred.stlouisfed.org/series/SPASTT01EZM661N) | Euro-area 19-country share-price aggregate |
| US government yield | [GS10 — Federal Reserve](https://fred.stlouisfed.org/series/GS10) | 10-year Treasury benchmark yield |
| Euro-area government yield | [IRLTLT01EZM156N — OECD](https://fred.stlouisfed.org/series/IRLTLT01EZM156N) | Euro-area 19-country 10-year benchmark yield |
| US corporate yield | [HQMCB7YR — US Treasury](https://fred.stlouisfed.org/series/HQMCB7YR) | High-quality 7-year corporate spot yield, AAA/AA/A |
| EUR corporate yield proxy | [BBSIS.M.I.UMR.RD.EUR.X2000.B.A.A.R.A.A._Z._Z.A — Deutsche Bundesbank](https://api.statistiken.bundesbank.de/rest/download/BBSIS/M.I.UMR.RD.EUR.X2000.B.A.A.R.A.A._Z._Z.A?format=csv&lang=en) | German corporate bonds, non-MFIs, monthly average; scope changed 1 May 2020 |

OECD attribution: OECD (2026), Main Economic Indicators / Financial Market share prices and long-term interest rates, [OECD Data Explorer](https://data-explorer.oecd.org/), retrieved through FRED, accessed 8 November 2026. ECB, Eurostat, BLS, BEA, Federal Reserve, US Treasury and Deutsche Bundesbank inputs are credited individually above. Source data and revisions remain the responsibility of their original publishers; no publisher endorses these app estimates.

Twelve country price indices use the same OECD series family, `SPASTT01{country code}M661N`: [FI](https://fred.stlouisfed.org/series/SPASTT01FIM661N), [EE](https://fred.stlouisfed.org/series/SPASTT01EEM661N), [IE](https://fred.stlouisfed.org/series/SPASTT01IEM661N), [NL](https://fred.stlouisfed.org/series/SPASTT01NLM661N), [BE](https://fred.stlouisfed.org/series/SPASTT01BEM661N), [DE](https://fred.stlouisfed.org/series/SPASTT01DEM661N), [FR](https://fred.stlouisfed.org/series/SPASTT01FRM661N), [AT](https://fred.stlouisfed.org/series/SPASTT01ATM661N), [PT](https://fred.stlouisfed.org/series/SPASTT01PTM661N), [ES](https://fred.stlouisfed.org/series/SPASTT01ESM661N), [IT](https://fred.stlouisfed.org/series/SPASTT01ITM661N), [GR](https://fred.stlouisfed.org/series/SPASTT01GRM661N). Latvia and Lithuania use the euro-area aggregate proxy, explicitly flagged in the app; no country-specific estimates were fabricated for those two markets.

## Asset interpretation and proxies

**Broad stocks** is a synthetic 50/50 average of the US and euro-area local-market price changes, not a worldwide index or a currency-translated portfolio return. Its slopes are the corresponding average of the two fitted regional slopes. **EUR stocks average** is the OECD euro-area aggregate, not an arithmetic average across the map's countries.

For the four bond assets, price-change histories were **constructed from actual historical yields**:

`synthetic repricing (%) = 100 × [((1 + previous quarterly yield/100)/(1 + current quarterly yield/100))^T − 1]`

Use T=10 years for US and euro-area government bonds, T=7 years for US corporate bonds, and an explicitly assumed T=5 years for the German corporate proxy. This is fixed-tenor zero-coupon repricing, treating yields as flat annually compounded discount yields. Treasury par yields, OECD government benchmark yields and German corporate portfolio yields are not zero-coupon spot curves, so their transformation is an approximation. Treasury's HQM series is a fitted spot yield.

These **are not observed bond-index return histories**, market-average durations, coupon-bond valuations or total returns. The German series is a limited proxy for EUR corporate bonds and excludes bank bonds; it cannot represent the complete euro-area corporate universe. Bond default coefficients therefore combine a historical yield association with a stated pricing assumption. The chart and two explanation tabs direct readers to these definitions. Default additional duration and convexity are zero, preventing a second direct rate effect from being silently added. Users may choose an explicit US/EU rate for a custom bond overlay.

## Why signs may differ from intuition

US stocks' US-rate coefficient is positive in this quarterly specification. It reflects co-movement and the model's controls, not a causal benefit from raising rates. The Federal Reserve's [Bernanke–Kuttner study](https://www.federalreserve.gov/econres/feds/what-explains-the-stock-market39s-reaction-to-federal-reserve-policy.htm) instead studies unexpected policy changes around events and reports roughly a 1% equity increase for a surprise 25 bp cut. Its identification, window and sample differ from this app's regression. The [ECB's policy-versus-information research](https://www.ecb.europa.eu/press/research-publications/resbull/2018/html/ecb.rb180921.el.html) also explains why rate/stock co-movement need not identify a policy effect.

Default slopes are sensitive to the sample, crises, factor correlations, revisions and omitted variables. Contemporaneous GDP/inflation releases arrive with delays, so these are not real-time tradable predictors. Separate US/euro-area rates, inflation, unemployment and GDP are modeled. Currency inputs were removed and all regressions were refitted; old currency coefficients were not reassigned. Euro-area unemployment uses the currently available Eurostat EA21 composition, while GDP, inflation and stock prices use EA19. That geographic mismatch is a proxy limitation. Unemployment is downloaded directly from Eurostat with the filters in the source ledger; the source-download script normalizes its JSON-stat response into monthly CSV. Negative inflation shocks mean falling inflation relative to baseline, not necessarily deflation. Positive stock-inflation coefficients are explicit scenario assumptions, not a general economic law. Nothing here establishes a causal response, stable forecast, expected investment return or probability.


## Map data

Boundaries come from [Natural Earth 1:110m Admin 0 Countries](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_admin_0_countries.geojson), available under [public-domain terms](https://www.naturalearthdata.com/about/terms-of-use/). The bundled map uses Mercator projection and clips to latitudes 15–80. Small islands and inland-water holes may be omitted. Boundaries follow the source's cartographic conventions.

## Additional markets

Sweden, Poland, Norway, Russia and the UK use explicit euro-area equity proxies. Each local-rate coefficient is −4.83% per +1 pp; its ECB coefficient is −2.42%. Other assets have zero exposure to these local-rate shocks by default. These are editable assumptions, not local empirical estimates. US/euro-area inflation, jobs and GDP inputs remain external regional proxies. Russia's model omits sanctions, closures, capital controls and investability. Latvia and Lithuania also use the euro-area reference. The US uses the existing US stock model.
