import copy
import unittest
from model import DEFAULT_ASSETS, validate_session
from timeline_model import MODES, quarter_index, quarter_label, validate_timeline, missing_quarters, fill_gaps, series_for
from themes import THEMES

class TimelineTests(unittest.TestCase):
    def point(self,quarter='2026-Q4',shock=1,name='Test'):
        return dict(quarter=quarter,name=name,shocks=[shock]+[0]*12)
    def asset(self,coef=10):
        return dict(name='Test asset',kind='Equity',sens=[coef]+[0]*12,duration=0,convexity=0,rate_region='US')

    def test_quarter_sort_and_year_boundary(self):
        points=validate_timeline([self.point('2027-Q2'),self.point('2026-Q4')])
        self.assertEqual([p['quarter'] for p in points],['2026-Q4','2027-Q2'])
        self.assertEqual(quarter_label(quarter_index('2026-Q4')+1),'2027-Q1')
        self.assertEqual(missing_quarters(points),['2027-Q1'])

    def test_effects_are_independent_no_implicit_compounding(self):
        result=series_for(self.asset(),[self.point('2026-Q4'),self.point('2027-Q2',2)])
        self.assertEqual([row[1] for row in result],[0,10,20])
        self.assertEqual(result[0][0],'2026-Q3')

    def test_compounding_requires_explicit_gap_fill(self):
        points=[self.point('2026-Q4'),self.point('2027-Q2',2)]
        with self.assertRaisesRegex(ValueError,'every quarter'):series_for(self.asset(),points,MODES[1])
        filled=fill_gaps(points)
        self.assertEqual(filled[1]['shocks'],[0]*13)
        self.assertIn('explicit',filled[1]['name'])
        levels=[r[1] for r in series_for(self.asset(),filled,MODES[1])]
        for actual,expected in zip(levels,[100,110,110,132]):self.assertAlmostEqual(actual,expected)
        self.assertEqual(len(points),2)

    def test_drop_and_recovery_and_total_loss(self):
        levels=series_for(self.asset(),[self.point('2026-Q4',-2),self.point('2027-Q1',2.5)],MODES[1])
        self.assertAlmostEqual(levels[-1][1],100)
        levels=series_for(self.asset(-100),[self.point('2026-Q4'),self.point('2027-Q1',-1)],MODES[1])
        self.assertEqual(levels[-1][1],0)
        with self.assertRaisesRegex(ValueError,'below −100'):series_for(self.asset(-100),[self.point(shock=2)],MODES[1])

    def test_invalid_dates_duplicates_and_limits(self):
        for quarter in ('Q4 2026','2026-Q5','1800-Q1','2201-Q1','2026-Q0'):
            with self.assertRaises(ValueError):validate_timeline([self.point(quarter)])
        with self.assertRaises(ValueError):validate_timeline([self.point(),self.point()])
        with self.assertRaises(ValueError):validate_timeline([self.point('2026-Q4'),self.point('2047-Q1')])
        with self.assertRaises(ValueError):validate_timeline([self.point(shock=float('nan'))])
        self.assertEqual(series_for(self.asset(),[],MODES[0]),[])
        self.assertEqual(series_for(self.asset(),[self.point('1900-Q1')])[0][0],'1899-Q4')

    def test_old_currency_sessions_rejected_and_v3_roundtrip(self):
        old=dict(version=3,assets=copy.deepcopy(DEFAULT_ASSETS),shocks=[0]*13,scenarios=[])
        for version in (3,4):
            old['version']=version
            with self.assertRaisesRegex(ValueError,'currency factors'):validate_session(old)
        old['version']=6
        new=validate_session(old)
        self.assertEqual(new['version'],6);self.assertEqual(new['timeline'],[]);self.assertEqual(new['theme'],'Forest')
        new.update(timeline=[self.point()],theme='Forest',timeline_mode=MODES[1])
        self.assertEqual(validate_session(new),new)
        for field,value in [('theme','Unknown'),('timeline_mode','Unknown'),('theme',[])]:
            broken=copy.deepcopy(new);broken[field]=value
            with self.assertRaises(ValueError):validate_session(broken)

    def test_theme_changes_cannot_change_numbers(self):
        reference=series_for(self.asset(),[self.point()])
        for theme in THEMES:
            session=validate_session(dict(version=6,assets=[self.asset()],shocks=[0]*13,scenarios=[],timeline=[self.point()],theme=theme))
            self.assertEqual(series_for(session['assets'][0],session['timeline']),reference)
        self.assertEqual(set(THEMES),{'Forest','Forest','Forest'})
        for p in THEMES.values():
            self.assertNotEqual(p['surface'],p['ink'])
            self.assertTrue(all(len(color)==7 and color.startswith('#') for color in p.values()))

if __name__=='__main__':unittest.main()
