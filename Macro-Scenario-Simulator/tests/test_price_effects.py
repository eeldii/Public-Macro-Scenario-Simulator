"""Exercise the Scenario lab rendering path without requiring a window server."""
import copy
import unittest
from types import SimpleNamespace
from app import App
from model import DEFAULT_ASSETS, FACTORS, PRICE_EFFECT_ASSETS, chart_results, estimate
from countries import EXTRA_MARKETS, asset_name
from themes import THEMES

class Table:
    def __init__(self): self.rows=[]
    def get_children(self): return list(range(len(self.rows)))
    def delete(self,*args): self.rows=[]
    def insert(self,*args,values): self.rows.append(values)

class Chart:
    def __init__(self): self.text=[]
    def delete(self,*args): self.text=[]
    def winfo_width(self): return 900
    def create_line(self,*args,**kwargs): pass
    def create_rectangle(self,*args,**kwargs): pass
    def create_text(self,*args,**kwargs): self.text.append(kwargs['text'])

class PriceEffectsTests(unittest.TestCase):
    def test_each_local_slider_updates_visible_chart_and_first_table_row(self):
        app=SimpleNamespace(assets=copy.deepcopy(DEFAULT_ASSETS),results=Table(),chart=Chart(),validation=SimpleNamespace(set=lambda value:None),palette=THEMES['Forest'])
        for index,country in enumerate(EXTRA_MARKETS,8):
            for change in (1,-1):
                shocks=[0]*len(FACTORS);shocks[index]=change
                app.shocks=lambda:shocks
                App.calculate(app)
                asset=next(a for a in app.assets if a['name']==asset_name(country))
                expected=estimate(asset,shocks)[1]
                self.assertEqual(app.results.rows[0][:2],(asset_name(country),f'{expected:+.2f}'))
                self.assertEqual(float(app.results.rows[0][index+2]),expected)
                self.assertIn(asset_name(country),app.chart.text)
                self.assertIn(f'{expected:+.1f}',app.chart.text)
                self.assertTrue(all(name in app.chart.text for name in PRICE_EFFECT_ASSETS))

    def test_missing_country_stays_visible_as_unavailable(self):
        assets=[a for a in DEFAULT_ASSETS if a['name']!='Sweden stocks']
        results=dict(chart_results(assets,[0]*len(FACTORS),PRICE_EFFECT_ASSETS))
        self.assertIsNone(results['Sweden stocks'])
        self.assertEqual(len(results),12)

if __name__=='__main__': unittest.main()
