"""Exercise real map event handlers against a recording canvas, without a display.
Catches item destruction/rebinding during click dispatch; optional GUI smoke test
still verifies the native Tk integration on a regular desktop.
"""
import copy
from types import SimpleNamespace
import unittest
from countries import COUNTRIES
from map_geometry import load_boundaries
from model import DEFAULT_ASSETS
from views import CountryMap, tooltip_position

class Value:
    def __init__(self): self.value=''
    def set(self, value): self.value=value

class RecordingCanvas:
    def __init__(self):
        self.items={}; self.bindings={}; self.binding_count=0; self.coordinate_updates=0
    def create_polygon(self, *coords, **options):return self.create(coords,options)
    def create_text(self, *coords, **options):return self.create(coords,options)
    def create(self,coords,options):
        key=len(self.items)+1
        self.items[key]=dict(coords=coords,options=options)
        return key
    def tag_bind(self,tag,event,callback):
        self.bindings[tag,event]=callback;self.binding_count+=1
    def itemconfigure(self,item,**options):self.items[item]['options'].update(options)
    def coords(self,item,*coords):
        self.items[item]['coords']=coords;self.coordinate_updates+=1
    def winfo_width(self):return 1000
    def winfo_height(self):return 600
    def delete(self,*_):raise AssertionError('Map items must survive pointer callbacks')

class Tooltip:
    def __init__(self): self.options={}; self.position=None
    def configure(self, **options): self.options.update(options)
    def winfo_reqwidth(self): return 240
    def winfo_reqheight(self): return 220
    def place(self, **position): self.position=position
    def place_forget(self): self.position=None
    def lift(self): pass

class MapInteractions(unittest.TestCase):
    def setUp(self):
        self.map=object.__new__(CountryMap)
        self.map.canvas=RecordingCanvas();self.map.info=Value();self.map.choice=Value()
        self.map.app=SimpleNamespace(assets=copy.deepcopy(DEFAULT_ASSETS),shocks=lambda:[0]*13)
        self.map.boundaries=load_boundaries();self.map.selected='Finland'
        self.map.zoom=1;self.map.pan=[0,0];self.map.drag_anchor=None
        self.map._tooltip=Tooltip();self.map._hover_country=None
        self.map._build_scene();self.map.refresh()

    def test_repeated_bound_clicks_preserve_items_bindings_and_geometry(self):
        canvas=self.map.canvas
        original_ids=set(canvas.items);bindings=canvas.binding_count;coords=canvas.coordinate_updates
        for _ in range(25):
            for code,country,*_ in COUNTRIES:
                canvas.bindings['country_'+code,'<Button-1>'](SimpleNamespace())
                self.assertEqual(self.map.selected,country)
                self.assertIn(country,self.map.info.value)
                canvas.bindings['label_'+code,'<Button-1>'](SimpleNamespace())
        self.assertEqual(set(canvas.items),original_ids)
        self.assertEqual(canvas.binding_count,bindings)
        self.assertEqual(canvas.coordinate_updates,coords)

    def test_hover_follows_cursor_and_hides_without_recreating_items(self):
        canvas=self.map.canvas;ids=set(canvas.items)
        canvas.bindings['country_FI','<Enter>'](SimpleNamespace(x=400,y=200))
        self.assertIn('Finland',self.map._tooltip.options['text'])
        self.assertIn('US rates:',self.map._tooltip.options['text'])
        self.assertEqual(self.map._tooltip.position,dict(x=416,y=218))
        canvas.bindings['country_FI','<Motion>'](SimpleNamespace(x=950,y=580))
        self.assertEqual(self.map._tooltip.position,dict(x=694,y=342))
        canvas.bindings['country_FI','<Leave>'](SimpleNamespace())
        self.assertIsNone(self.map._tooltip.position)
        self.assertEqual(set(canvas.items),ids)

    def test_tooltip_missing_invalid_and_proxy_results(self):
        self.assertIn('Euro-area proxy',self.map.tooltip_text('Latvia'))
        self.assertIn('No modeled result',self.map.tooltip_text('Canada'))
        def invalid():raise ValueError('Invalid input')
        self.map.app.shocks=invalid
        self.assertIn('invalid',self.map.tooltip_text('Finland'))

    def test_tooltip_position_stays_in_normal_viewport(self):
        for x,y in ((0,0),(999,599),(500,300),(999,0),(0,599)):
            left,top=tooltip_position(x,y,240,220,1000,600)
            self.assertGreaterEqual(left,0);self.assertGreaterEqual(top,0)
            self.assertLessEqual(left+240,1000);self.assertLessEqual(top+220,600)

    def test_zoom_pan_and_reset_preserve_items(self):
        ids=set(self.map.canvas.items)
        self.map.change_zoom(1.25)
        self.map.drag_anchor=(10,10);self.map.drag(SimpleNamespace(x=20,y=30))
        self.assertEqual(self.map.pan,[10,20])
        self.map.reset_view()
        self.assertEqual(self.map.pan,[0,0]);self.assertEqual(self.map.zoom,1)
        self.assertEqual(set(self.map.canvas.items),ids)

    def test_invalid_inputs_and_removed_country_do_not_destroy_scene(self):
        ids=set(self.map.canvas.items)
        def invalid():raise ValueError('Bad shock')
        self.map.app.shocks=invalid;self.map.refresh()
        self.assertEqual(self.map.canvas.items[self.map._error]['options']['state'],'normal')
        self.map.app.shocks=lambda:[0]*13
        self.map.app.assets=[a for a in self.map.app.assets if a['name']!='Finland stocks']
        self.map.select('Finland')
        self.assertIn('N/A',self.map.info.value)
        self.assertEqual(set(self.map.canvas.items),ids)

if __name__=='__main__':unittest.main()
