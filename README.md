# Macro Scenario Simulator

An offline Python desktop app for exploring how economic changes could affect stocks, bonds and selected companies. Built for macOS with a simple Forest-themed interface.

<img width="1701" height="955" alt="image" src="https://github.com/user-attachments/assets/dc2a1674-681d-4993-a8ea-ed8cec397e4c" />

## Features

- Adjust 13 economic shocks: US/euro-area interest rates, inflation, unemployment and GDP growth, plus policy-rate changes for Sweden, Poland, Norway, Russia and the UK.
- Explore 26 default assets and edit their sensitivities or add your own companies.
- Compare scenarios and plot quarterly timelines as baseline effects or a hypothetical compounded index.
- View country results on an interactive map with hover details, zoom and pan.
- Inspect the calculations and assumptions behind each result.
- Optionally save sessions locally and export results to CSV.

<img width="856" height="538" alt="macroscenarios" src="https://github.com/user-attachments/assets/989428dd-eb21-4b8b-a226-410b889de34a" />

## Run on macOS

1. Install **Python 3.10 or newer with Tk** from [python.org](https://www.python.org/downloads/macos/) if needed.
2. Download and extract this repository. Keep the files and `data` folder together.
3. Double-click **Start Macro Scenario Simulator.command**.

No pip packages, account, API key or internet connection are required for everyday use. The launcher opens through Terminal; keep that window open while using the app. If the launcher loses executable permission, open `app.py` with Python Launcher or run this once:

```sh
chmod +x "Start Macro Scenario Simulator.command"
```

Startup errors are logged locally to `~/Library/Logs/Macro Scenario Simulator.log`. This is a Python source application, not a signed standalone app bundle.

## How to use

Change the sliders in **Scenario lab** to see estimated price effects. Inputs are percentage-point changes from your baseline: a rate moving from 3% to 4% is a +1 pp shock. Inflation and GDP inputs are changes in year-on-year growth rates, not absolute levels.

Edit coefficients in **Assets & sensitivities**. Add named scenarios in **Comparisons**, or assign quarterly scenarios in **Timeline**. The compounded view requires a scenario for every intervening quarter; missing quarters are filled only when you explicitly request it.

## Assumptions and limitations

This public copy includes generic research-informed defaults, **no personal workbook settings, saved sessions or portfolios**. Fresh launches start with zero shocks and empty comparisons and timelines. Optional saves and exports stay on your computer.

Results are **illustrative scenarios, not forecasts or investment advice**. Public historical inputs cover 102 quarters, with additional configurable sign and proxy assumptions. The added European markets use explicit regional proxies, not country-specific historical estimates. The model omits many real-world effects and does not establish predictive accuracy.

See [Research.md](Research.md) for methodology, public data sources, attribution and limitations. Source data retain their original publishers' usage terms; Natural Earth map boundaries are public domain.

## Development

The app uses Python's standard library. Run the automated tests from the repository folder:

```sh
python3 -m unittest discover -s tests -v
```

The `research` folder contains the historical input panel and scripts for reproducing the reference calibration. Source downloads are optional developer tools and never run during app startup.

Automated model, timeline, chart and map-handler tests are included. Native macOS appearance and Finder startup still require manual desktop verification. An optional check is available with `python3 tests/gui_smoke.py`.
