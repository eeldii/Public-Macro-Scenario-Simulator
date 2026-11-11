"""Optional real-desktop smoke check; not part of headless test discovery."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import App
from model import PRESETS, FACTORS, DEFAULT_ASSETS
app = App()
try:
    app.update()
    assert len(app.results.get_children()) == len(DEFAULT_ASSETS)
    app.set_shocks(PRESETS['Illustrative recession'])
    app.scenarios.append({'name': 'Recession', 'shocks': PRESETS['Illustrative recession']})
    app.refresh_compare()
    app.update()
    assert len(app.comp.get_children()) == 1
    assert len(app.matrix.get_children()) == len(DEFAULT_ASSETS)
    app.vars[0].set('bad')
    app.update()
    assert 'number' in app.validation.get()
    assert not app.results.get_children()
    app.set_shocks([0]*len(FACTORS))
    app.update()
    assert len(app.results.get_children()) == len(DEFAULT_ASSETS)
    assert app.slider_vars[0].get() == 0
    app.tabs.select(app.country_map)
    app.update()
    from countries import COUNTRIES
    original_items = app.country_map.canvas.find_all()
    for _ in range(10):
        for code, country, *_ in COUNTRIES:
            items = app.country_map.canvas.find_withtag('country_' + code)
            assert items
            # Exercise selection handlers while preserving native canvas items.
            app.country_map.select(country)
            app.update()
    assert app.country_map.canvas.find_all() == original_items
    app.country_map.select('Finland')
    assert 'Finland' in app.country_map.info.get()
    app.tabs.select(app.explanation)
    app.explanation.refresh()
    assert 'HISTORICALLY INFORMED SCENARIO DEFAULTS' in app.explanation.text.get('1.0', 'end')
    assert app.tabs.index(app.country_map) == app.tabs.index(app.assumptions) + 1
    assert app.tabs.index(app.help) == app.tabs.index(app.country_map) + 1
    app.country_map.change_zoom(1.25)
    app.country_map.reset_view()
    assert app.country_map.zoom == 1
    app.set_shocks([0, 1, 0, 0, 0, 0, 0, 0])
    app.explanation.refresh()
    assert 'Euro-area interest rate change' in app.explanation.text.get('1.0', 'end')
    from timeline_model import MODES
    app.tabs.select(app.timeline)
    app.timeline_points = [dict(quarter='2026-Q4', name='First', shocks=[1]+[0]*12), dict(quarter='2027-Q2', name='Second', shocks=[0,1]+[0]*11)]
    app.timeline.refresh(); app.update()
    assert len(app.timeline.table.get_children()) == 2
    app.timeline.mode.set(MODES[1]); app.timeline.refresh(); app.update()
    app.timeline.fill(); app.update()
    assert len(app.timeline_points) == 3
    for theme in ('Forest', 'Forest', 'Forest'):
        app.theme_var.set(theme); app.change_theme(); app.update()
        assert app.palette['bg'] == app.cget('bg')
    assert app.session()['theme'] == 'Forest'
    assert len(app.session()['timeline']) == 3
    print('GUI smoke checks passed')
finally:
    app.destroy()
