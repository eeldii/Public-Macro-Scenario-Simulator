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


### How to run on macOS, how to use, and assumptions and limitations 

All explained in README.md, found in the GitHub repository.
