# Macro Scenario Simulator Documentation

Tracking and predicting the effects of macroeconomic shocks is difficult. I wanted to build a simple program that lets users simulate different shocks and see how they might affect a range of financial assets.

Realistically modeling these effects is much harder, so I built the simulator as a practice project to learn how to develop forecasting tools. The results are illustrative. The default asset sensitivities are based on historical averages, with some values simplified.

<img width="3402" height="1910" alt="image" src="https://github.com/user-attachments/assets/820f01a2-323a-4e94-8dba-9c7ebc3dc47c" />

# The program

The Macro Scenario Simulator is a Python desktop app built for macOS. It has a simple, light-themed interface and uses Python’s standard library. See `Research.md` for the methodology, public data sources, attribution, and limitations.

I started with a rough outline of what I wanted the app to do. The finished app follows that outline and includes several features I added along the way. I also used Excel to manually correct and simplify some of the historical asset sensitivity estimates.

<img width="1712" height="1076" alt="image" src="https://github.com/user-attachments/assets/0599bea7-2587-4fba-a488-a7c8210509ac" />

## Features

- Adjust 13 economic shocks covering interest rates, inflation, unemployment, and GDP growth in the US and the euro area, plus policy rate changes in Sweden, Poland, Norway, Russia, and the UK.
- Explore 26 default assets, edit their sensitivities, or add your own companies.
- Compare scenarios and chart quarterly results as baseline effects or as a hypothetical compounded index.
- Explore country-level results on an interactive map with hover details, zoom, and pan.
- Review the calculations and assumptions behind each result.
- Save sessions locally and export results to CSV.

## Getting started

See `README.md` in the GitHub repository for instructions on running the app on macOS and using its features. The model’s assumptions and limitations are documented in `Research.md`.
