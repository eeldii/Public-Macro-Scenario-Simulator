import copy
import csv
import importlib.util
import json
import math
from pathlib import Path
import unittest
from model import (FACTORS, DEFAULT_ASSETS, RESEARCH_ASSETS, BASE_ASSET_SOURCE, load_base_assets, PRESETS, CALIBRATION, CHART_ASSETS, PROVENANCE,
                   chart_results, default_status, estimate, validate_session, validate_shocks)
from countries import COUNTRIES, asset_name, effect_color
from map_geometry import BOUNDS, clip_ring, load_boundaries, project, viewport

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('calibrate',ROOT/'research/calibrate.py')
calibrate=importlib.util.module_from_spec(spec);spec.loader.exec_module(calibrate)

class ModelTests(unittest.TestCase):
    def shock(self,**kwargs):return [kwargs.get(k,0) for k in FACTORS]

    def test_all_defaults_and_presets_valid(self):
        self.assertEqual(len({a['name'] for a in DEFAULT_ASSETS}),len(DEFAULT_ASSETS))
        for a in DEFAULT_ASSETS:
            self.assertTrue(default_status(a))
            self.assertEqual(estimate(a,self.shock())[1],0)
        for preset in PRESETS.values():validate_shocks(preset)

    def test_stock_rates_follow_negative_scenario_convention(self):
        for asset in DEFAULT_ASSETS:
            if asset['kind'] == 'Equity':
                for factor in ('us_rates', 'eu_rates'):
                    with self.subTest(asset=asset['name'], factor=factor):
                        self.assertLess(estimate(asset, self.shock(**{factor: 1}))[1], 0)
                        self.assertGreater(estimate(asset, self.shock(**{factor: -1}))[1], 0)
                        self.assertEqual(estimate(asset, self.shock())[1], 0)

    def test_stock_inflation_direction_and_bond_fit_preserved(self):
        for asset in RESEARCH_ASSETS:
            if asset['kind'] == 'Equity':
                for factor in ('us_inflation', 'eu_inflation'):
                    with self.subTest(asset=asset['name'], factor=factor):
                        self.assertGreater(estimate(asset, self.shock(**{factor: 1}))[1], 0)
                        self.assertLess(estimate(asset, self.shock(**{factor: -1}))[1], 0)
            else:
                self.assertEqual(asset['sens'][:6], [round(v,2) for v in CALIBRATION['models'][asset['name']]['coefficients'][:6]])

    def test_separate_regional_cycle_inputs(self):
        self.assertEqual(FACTORS[:8], ('us_rates','eu_rates','us_inflation','eu_inflation','us_unemployment','eu_unemployment','us_gdp','eu_gdp'))
        self.assertEqual(tuple(CALIBRATION['factors']), FACTORS[:8])
        for asset in DEFAULT_ASSETS:
            for index in range(4,8):
                shock=[0]*13; shock[index]=1
                parts,total=estimate(asset,shock)
                self.assertAlmostEqual(total,asset['sens'][index])
                self.assertEqual(sum(v != 0 for i,v in enumerate(parts) if i != index),0)
        for factor,limit in [('eu_unemployment',15),('us_gdp',20),('eu_gdp',20)]:
            validate_shocks(self.shock(**{factor: limit}))
            with self.assertRaises(ValueError):validate_shocks(self.shock(**{factor: limit+0.1}))

    def test_local_rates_only_affect_linked_proxy_by_default(self):
        names=('Sweden','Poland','Norway','Russia','United Kingdom')
        for index,country in enumerate(names,8):
            shocks=[0]*13;shocks[index]=1
            affected=[a['name'] for a in DEFAULT_ASSETS if estimate(a,shocks)[1]!=0]
            self.assertEqual(affected,[asset_name(country)])
            a=next(a for a in DEFAULT_ASSETS if a['name']==asset_name(country))
            self.assertLess(estimate(a,shocks)[1],0)
            shocks[index]=-1;self.assertGreater(estimate(a,shocks)[1],0)
        self.assertEqual(sum(a['name']=='US stocks' for a in DEFAULT_ASSETS),1)

    def test_format5_migration_preserves_results_and_timeline(self):
        asset=copy.deepcopy(DEFAULT_ASSETS[2]);asset['sens']=asset['sens'][:8]
        shocks=[1,-1,0.5,0,0,0,1,0]
        old=dict(version=5,assets=[asset],shocks=shocks,scenarios=[dict(name='Saved',shocks=shocks)],timeline=[dict(quarter='2027-Q1',name='Saved',shocks=shocks)],theme='Forest')
        new=validate_session(old)
        self.assertEqual(new['version'],6)
        self.assertEqual(new['shocks'],shocks+[0]*5)
        self.assertEqual(new['timeline'][0]['shocks'],shocks+[0]*5)
        self.assertAlmostEqual(estimate(new['assets'][0],new['shocks'])[1],sum(x*y for x,y in zip(asset['sens'],shocks)))
        self.assertEqual(len(old['assets'][0]['sens']),8)

    def test_public_defaults_match_research_scenario_assumptions(self):
        self.assertEqual(DEFAULT_ASSETS,BASE_ASSET_SOURCE['assets'])
        self.assertEqual(len(DEFAULT_ASSETS),26)
        us=next(a for a in DEFAULT_ASSETS if a['name']=='US stocks')
        self.assertEqual(DEFAULT_ASSETS,RESEARCH_ASSETS)
        self.assertAlmostEqual(estimate(us,self.shock(us_rates=1))[1],us['sens'][0])
        self.assertEqual(load_base_assets(BASE_ASSET_SOURCE),DEFAULT_ASSETS)

    def test_base_loader_rejects_mismatched_or_invalid_inputs(self):
        for change in ('factors','duplicate','nan'):
            broken=copy.deepcopy(BASE_ASSET_SOURCE)
            if change=='factors':broken['factors'].reverse()
            if change=='duplicate':broken['assets'][1]['name']=broken['assets'][0]['name']
            if change=='nan':broken['assets'][0]['sens'][0]=float('nan')
            with self.assertRaises(ValueError):load_base_assets(broken)

    def test_public_provenance_distinguishes_research(self):
        from research_notes import provenance_text
        self.assertIn('PUBLIC BASE ASSUMPTIONS',provenance_text(DEFAULT_ASSETS[0]))
        custom=copy.deepcopy(DEFAULT_ASSETS[0]);custom['sens'][0]+=1
        self.assertIn('CUSTOM ASSUMPTIONS',provenance_text(custom))

    def test_gdp_directions_for_both_regions(self):
        for asset in RESEARCH_ASSETS:
            for factor in ('us_gdp','eu_gdp'):
                sign=-1 if asset['kind']=='Bond' else 1
                self.assertGreater(sign*estimate(asset,self.shock(**{factor:1}))[1],0)
                self.assertLess(sign*estimate(asset,self.shock(**{factor:-1}))[1],0)

    def test_map_colour_has_stronger_small_change_contrast(self):
        colors=[effect_color(v) for v in (0,0.5,1,2,5,10)]
        self.assertEqual(len(set(colors)),6)
        self.assertEqual(effect_color(10),effect_color(100))
        self.assertEqual(effect_color(-10),effect_color(-100))

    def test_domestic_rate_effects_dominate_foreign_effects(self):
        assets = {a['name']: a for a in DEFAULT_ASSETS}
        us, eu = assets['US stocks'], assets['EUR stocks average']
        self.assertGreater(abs(us['sens'][0]), abs(eu['sens'][0]))
        self.assertGreater(abs(eu['sens'][1]), abs(us['sens'][1]))
        self.assertGreater(abs(us['sens'][0]), abs(us['sens'][1]))
        for code, country, *_ in COUNTRIES:
            if code in ('US','SE','PL','NO','RU','GB'): continue
            asset = assets[asset_name(country)]
            self.assertGreater(abs(asset['sens'][1]), abs(asset['sens'][0]))
            self.assertLess(abs(asset['sens'][0]), abs(us['sens'][0]))

    def test_sensitivity_rounding_is_used_in_calculation(self):
        from model import validate_asset
        for asset in DEFAULT_ASSETS:
            self.assertTrue(all(v == round(v, 2) for v in asset['sens']))
        custom = copy.deepcopy(DEFAULT_ASSETS[0])
        custom['sens'][0] = 3.14159
        self.assertEqual(validate_asset(custom)['sens'][0], 3.14)
        self.assertEqual(estimate(custom, self.shock(us_rates=1))[1], 3.14)

    def test_separate_us_and_eu_rates(self):
        for a in DEFAULT_ASSETS:
            self.assertAlmostEqual(estimate(a,self.shock(us_rates=1))[1],a['sens'][0])
            self.assertAlmostEqual(estimate(a,self.shock(eu_rates=1))[1],a['sens'][1])
        a=DEFAULT_ASSETS[2]
        self.assertNotEqual(estimate(a,self.shock(us_rates=1))[1],estimate(a,self.shock(eu_rates=1))[1])

    def test_regional_bonds_exist_and_have_eight_factors(self):
        by_name={a['name']:a for a in DEFAULT_ASSETS}
        for name in CHART_ASSETS[3:]:
            self.assertEqual(by_name[name]['kind'],'Bond')
            self.assertEqual(len(by_name[name]['sens']),13)
            self.assertEqual(by_name[name]['duration'],0)
        self.assertEqual(by_name['EUR corporate bonds']['rate_region'],'EU')

    def test_optional_bond_overlay_uses_correct_region(self):
        a=dict(name='Custom',kind='Bond',sens=[0]*13,duration=7,convexity=60,rate_region='EU')
        self.assertEqual(estimate(a,self.shock(us_rates=1))[1],0)
        self.assertAlmostEqual(estimate(a,self.shock(eu_rates=1))[1],-6.7)
        a['rate_region']='US'
        self.assertEqual(estimate(a,self.shock(eu_rates=1))[1],0)
        self.assertAlmostEqual(estimate(a,self.shock(us_rates=-1))[1],7.3)

    def test_contributions_sum_and_zero_drift(self):
        shocks=self.shock(us_rates=0.5,eu_rates=-0.25,us_inflation=1,eu_unemployment=2,eu_gdp=-1,us_gdp=-0.3)
        for a in DEFAULT_ASSETS:
            parts,total=estimate(a,shocks)
            self.assertEqual(total,sum(parts))
            self.assertAlmostEqual(total,sum(v*x for v,x in zip(a['sens'],shocks)))

    def test_chart_order_not_asset_list_order(self):
        assets=list(reversed(DEFAULT_ASSETS))
        self.assertEqual([n for n,_ in chart_results(assets,self.shock())],list(CHART_ASSETS))
        assets=[a for a in assets if a['name']!=CHART_ASSETS[1]]
        rows=chart_results(assets,self.shock())
        self.assertIsNone(rows[1][1]);self.assertEqual(len(rows),7)

    def test_invalid_inputs_and_schema(self):
        for values in ([0]*12,self.shock(us_rates=float('nan')),self.shock(eu_rates=11),self.shock(eu_gdp=float('inf'))):
            with self.assertRaises(ValueError):validate_shocks(values)
        for version in (1,2,3,4):
            with self.assertRaisesRegex(ValueError,'Session format 5 required'):validate_session(dict(version=version))

    def test_session_roundtrip_and_duplicates(self):
        data=dict(version=6,assets=copy.deepcopy(DEFAULT_ASSETS),shocks=self.shock(us_unemployment=1,eu_unemployment=-2,us_gdp=3,eu_gdp=-4),scenarios=[dict(name='EU only',shocks=self.shock(eu_rates=1,eu_gdp=2))],timeline=[dict(quarter='2027-Q2',name='Regional changes',shocks=self.shock(eu_unemployment=0.5,eu_gdp=-1))],theme='Forest',timeline_mode='Scenario effects (%)')
        self.assertEqual(validate_session(json.loads(json.dumps(data))),data)
        data['assets'][1]['name']=data['assets'][0]['name']
        with self.assertRaises(ValueError):validate_session(data)

    def test_custom_coefficients_lose_default_label(self):
        a=copy.deepcopy(DEFAULT_ASSETS[0]);a['sens'][0]+=1
        self.assertFalse(default_status(a))
        a=copy.deepcopy(DEFAULT_ASSETS[0]);a['name']='My firm'
        self.assertFalse(default_status(a))

    def test_country_proxies_are_explicit(self):
        for code,country,*_ in COUNTRIES:
            key=PROVENANCE[asset_name(country)]
            self.assertEqual(key,'US stocks' if code=='US' else 'EUR stocks average' if code in ('LV','LT','SE','PL','NO','RU','GB') else 'country_'+code)

    def test_extreme_estimates_not_clipped(self):
        a=copy.deepcopy(DEFAULT_ASSETS[0]);a['sens']=[-100]+[0]*12
        self.assertEqual(estimate(a,self.shock(us_rates=2))[1],-200)

class CalibrationTests(unittest.TestCase):
    def test_regression_recovers_known_coefficients(self):
        x=[[1,i,i*i] for i in range(-6,7)]
        y=[2+3*r[1]-0.5*r[2] for r in x]
        fit=calibrate.regress(x,y)
        self.assertEqual(fit['coefficients'],[3,-0.5]);self.assertAlmostEqual(fit['intercept'],2)
        self.assertAlmostEqual(fit['r_squared'],1)

    def test_bundled_coefficients_reproduce_from_panel(self):
        with (ROOT/'research/calibration_panel.csv').open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),102)
        self.assertEqual(rows[0]['quarter'],'2000-Q2');self.assertEqual(rows[-1]['quarter'],'2025-Q3')
        x=[[1,*[float(r[k]) for k in FACTORS[:8]]] for r in rows]
        for target,expected in CALIBRATION['models'].items():
            fit=calibrate.regress(x,[float(r[target]) for r in rows])
            recent=[r for r in rows if r['quarter'] >= '2015-Q4']
            self.assertEqual(len(recent),40)
            recent_fit=calibrate.regress([[1,*[float(r[k]) for k in FACTORS[:8]]] for r in recent],[float(r[target]) for r in recent])
            self.assertEqual(recent_fit['coefficients'],expected['recent_10_years'])
            for key in ('coefficients','intercept','hc1_se','n','r_squared'):
                self.assertEqual(fit[key],expected[key])

    def test_broad_blend_matches_regional_slopes(self):
        models=CALIBRATION['models']
        for broad,us,eu in zip(models['Broad stocks']['coefficients'],models['US stocks']['coefficients'],models['EUR stocks average']['coefficients']):
            self.assertAlmostEqual(broad,(us+eu)/2,places=5)

class GeographyTests(unittest.TestCase):
    def test_real_boundaries_cover_modeled_countries(self):
        boundaries=load_boundaries()
        self.assertTrue({c[0] for c in COUNTRIES}.issubset({f['iso'] for f in boundaries}))
        self.assertGreater(sum(len(ring) for f in boundaries for ring in f['rings']),1000)
        for f in boundaries:
            for ring in f['rings']:
                self.assertTrue(all(math.isfinite(x) and math.isfinite(y) for x,y in ring))

    def test_clipping_and_projection(self):
        clipped=clip_ring([(-50,20),(60,20),(60,80),(-50,80)])
        self.assertTrue(clipped)
        self.assertTrue(all(BOUNDS[0]<=x<=BOUNDS[2] and BOUNDS[1]<=y<=BOUNDS[3] for x,y in clipped))
        s,ox,oy=viewport(1000,650)
        for lon,lat in ((BOUNDS[0],BOUNDS[1]),(BOUNDS[2],BOUNDS[3])):
            x,y=project(lon,lat)
            self.assertTrue(0<=ox+x*s<=1000 and 0<=oy+y*s<=650)

    def test_colour_sign_and_saturation(self):
        self.assertNotEqual(effect_color(-1),effect_color(1))
        self.assertEqual(effect_color(0),'#e3e9ef')
        self.assertEqual(effect_color(-200),effect_color(-20))

if __name__=='__main__':unittest.main()
