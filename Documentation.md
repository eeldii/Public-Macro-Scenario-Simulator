# Macro Scenario Simulator Documentation

Tracking and prediciting the effects of macroeconomic shocks is hard. I wanted to try and build a simple program that simulates different shocks and shows how they affect different financial assets. 

A program that realistically simulates the outcomes is of course extremely difficult, if not impossible, to create. Because of that, this program is meant to be taken as a "practice project" for creating prediction calculators, not as an actual macro-predictor. Base asset sensitivities are based on historical averages and slight simplificiations of those averages.

# The program itself

It is a Python desktop app that was built for macOS with a simple light-themed interface. The app uses Python's standard library. See Research.md for methodology, public data sources, attribution and limitations.

## Features

- Adjust 13 economic shocks: US/euro-area interest rates, inflation, unemployment and GDP growth, plus policy-rate changes for Sweden, Poland, Norway, Russia and the UK.
- Explore 26 default assets and edit their sensitivities or add your own companies.
- Compare scenarios and plot quarterly timelines as baseline effects or a hypothetical compounded index.
- View country results on an interactive map with hover details, zoom and pan.
- Inspect the calculations and assumptions behind each result.
- Optionally save sessions locally and export results to CSV.


### How to run on macOS

1. Install **Python 3.10 or newer with Tk** from [python.org](https://www.python.org/downloads/macos/) if needed.
2. Download and extract this repository. Keep the files and `data` folder together.
3. Double-click **Start Macro Scenario Simulator.command**.

No pip packages, account, API key or internet connection are required for everyday use. The launcher opens through Terminal; keep that window open while using the app. If the launcher loses executable permission, open `app.py` with Python Launcher or run this once:

```sh
chmod +x "Start Macro Scenario Simulator.command"
```

Startup errors are logged locally to `~/Library/Logs/Macro Scenario Simulator.log`. This is a Python source application, not a signed standalone app bundle.

### How to use

Change the sliders in **Scenario lab** to see estimated price effects. Inputs are percentage-point changes from your baseline: a rate moving from 3% to 4% is a +1 pp shock. Inflation and GDP inputs are changes in year-on-year growth rates, not absolute levels.

Edit coefficients in **Assets & sensitivities**. Add named scenarios in **Comparisons**, or assign quarterly scenarios in **Timeline**. The compounded view requires a scenario for every intervening quarter; missing quarters are filled only when you explicitly request it.

### Assumptions and limitations

This public copy includes generic research-informed defaults, **no personal workbook settings, saved sessions or portfolios**. Fresh launches start with zero shocks and empty comparisons and timelines. Optional saves and exports stay on your computer.

Results are **illustrative scenarios, not forecasts or investment advice**. Public historical inputs cover 102 quarters, with additional configurable sign and proxy assumptions. The added European markets use explicit regional proxies, not country-specific historical estimates. The model omits many real-world effects and does not establish predictive accuracy.

See [Research.md](Research.md) for methodology, public data sources, attribution and limitations. Source data retain their original publishers' usage terms; Natural Earth map boundaries are public domain.
