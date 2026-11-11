"""Display-independent graph/controller integration checks."""
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from model import DEFAULT_ASSETS, CHART_ASSETS
from timeline_model import MODES
from timeline_view import Timeline
from themes import THEMES

class Var:
    def __init__(self,value=None):self.value=value
    def get(self):return self.value
    def set(self,value):self.value=value

class Canvas:
    def __init__(self):self.items=[]
    def configure(self,**_):pass
    def delete(self,*_):self.items=[]
    def create_text(self,*coords,**opts):self.items.append(('text',coords,opts))
    def create_line(self,*coords,**opts):self.items.append(('line',coords,opts))
    def create_oval(self,*coords,**opts):self.items.append(('oval',coords,opts))
    def winfo_width(self):return 1000
    def winfo_height(self):return 350

class TimelineViewTests(unittest.TestCase):
    def setUp(self):
        self.view=object.__new__(Timeline)
        self.view.app=SimpleNamespace(assets=copy.deepcopy(DEFAULT_ASSETS),timeline_points=[dict(quarter='2026-Q4',name='First',shocks=[1]+[0]*12),dict(quarter='2027-Q2',name='Second',shocks=[0,1]+[0]*11)],scenarios=[],palette=THEMES['Forest'],dirty=False,shocks=lambda:[1]+[0]*12)
        self.view.canvas=Canvas();self.view.info=Var();self.view.note=Var();self.view.mode=Var(MODES[0])
        self.view.enabled={name:Var(name=='US stocks') for name in CHART_ASSETS}
        self.view.source=Var('Current scenario lab');self.view.name=Var('Named point');self.view.year=Var('2026');self.view.quarter=Var('Q4');self.view.editing=None

    def test_graph_preserves_real_quarter_spacing_and_gap_markers(self):
        self.view.draw()
        points=self.view.hover_points
        self.assertEqual(len(points),3)
        # Baseline Q3 -> assigned Q4 is one quarter; Q4 -> Q2 is two quarters.
        self.assertAlmostEqual(points[2][0]-points[1][0],2*(points[1][0]-points[0][0]))
        self.assertTrue(any(kind=='line' and opts.get('dash')==(5,4) for kind,_,opts in self.view.canvas.items))

    def test_compound_graph_refuses_gaps_then_draws_after_explicit_fill(self):
        from timeline_model import fill_gaps
        self.view.mode.set(MODES[1]);self.view.draw()
        self.assertEqual(self.view.hover_points,[])
        self.assertTrue(any('every quarter' in opts.get('text','') for _,_,opts in self.view.canvas.items))
        self.view.app.timeline_points=fill_gaps(self.view.app.timeline_points);self.view.draw()
        self.assertEqual(len(self.view.hover_points),4)
        self.assertIn('index 100.00',self.view.hover_points[0][2])

    def test_add_snapshot_does_not_follow_later_lab_edits(self):
        self.view.app.timeline_points=[];self.view.refresh=lambda:None
        current=[1]+[0]*12;self.view.app.shocks=lambda:current
        self.view.add();current[0]=5
        self.assertEqual(self.view.app.timeline_points[0]['shocks'][0],1)
        self.assertTrue(self.view.app.dirty)
        with patch('timeline_view.messagebox.showerror') as error:
            self.view.add()
            error.assert_called_once()
        self.assertEqual(len(self.view.app.timeline_points),1)

if __name__=='__main__':unittest.main()
