#!/usr/bin/env python3
"""Macro Scenario Simulator — standard-library-only desktop application."""
import copy
import csv
import json
import os
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from model import DEFAULT_ASSETS, FACTORS, LABELS, SHORT_LABELS, LIMITS, PRESETS, CHART_ASSETS, PRICE_EFFECT_ASSETS, chart_results, estimate, validate_asset, validate_session, validate_shocks

BG = '#f3f6fa'
INK = '#142c45'
BLUE = '#2864c5'
GREEN = '#17836c'
RED = '#c04b58'

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Macro Scenario Simulator')
        self.geometry(f'{min(1380, self.winfo_screenwidth()-60)}x{min(1000, self.winfo_screenheight()-90)}')
        self.minsize(1050, 760)
        self.configure(bg=BG)
        self.assets = copy.deepcopy(DEFAULT_ASSETS)
        self.scenarios = []
        self.timeline_points = []
        from themes import THEMES
        self.palette = THEMES['Forest']
        self.theme_var = tk.StringVar(value='Forest')
        self.dirty = False
        self.filepath = None
        self.vars = [tk.StringVar(value='0') for _ in FACTORS]
        self.slider_vars = [tk.DoubleVar(value=0) for _ in FACTORS]
        self.status = tk.StringVar(value='Ready • Offline • Public research-informed assumptions')
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Helvetica', 12), background=BG, foreground=INK)
        style.configure('TButton', padding=(12, 7))
        style.configure('TNotebook.Tab', padding=(16, 10))
        style.configure('Treeview', rowheight=29, background='white', fieldbackground='white')
        style.configure('Treeview.Heading', font=('Helvetica', 11, 'bold'), padding=7)
        header = ttk.Frame(self, padding=(24, 18))
        header.pack(fill='x')
        ttk.Label(header, text='Macro Scenario Simulator', font=('Helvetica', 24, 'bold')).pack(anchor='w')
        ttk.Label(header, text='Explore macro shocks. Compare outcomes. Understand the assumptions.', foreground='#526a80').pack(anchor='w', pady=(6, 0))
        actions = ttk.Frame(self, padding=(24, 0, 24, 12))
        actions.pack(fill='x')
        for text, command in [('Save session…', self.save), ('Load session…', self.load), ('Export results…', self.export)]:
            ttk.Button(actions, text=text, command=command).pack(side='left', padx=(0, 8))
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill='both', expand=True, padx=24)
        self.explore = ttk.Frame(self.tabs, padding=16)
        self.compare = ttk.Frame(self.tabs, padding=16)
        self.assumptions = ttk.Frame(self.tabs, padding=16)
        self.help = ttk.Frame(self.tabs, padding=20)
        for frame, label in [(self.explore, 'Scenario lab'), (self.compare, 'Comparisons'), (self.assumptions, 'Assets & sensitivities'), (self.help, 'How it works')]:
            self.tabs.add(frame, text=label)
        self.build_explore()
        self.build_compare()
        self.build_assets()
        self.build_help()
        from views import Explanation, CountryMap
        self.explanation = Explanation(self.tabs, self)
        self.country_map = CountryMap(self.tabs, self)
        self.tabs.add(self.explanation, text='Calculations explained')
        self.tabs.insert(self.tabs.index(self.help), self.country_map, text='Country map')
        from timeline_view import Timeline
        self.timeline = Timeline(self.tabs, self)
        self.tabs.insert(2, self.timeline, text='Timeline')
        ttk.Label(self, text='SCENARIO ASSUMPTIONS • Higher rates reduce stock estimates • Not causal forecasts • No live data', foreground=RED, padding=(24, 9)).pack(anchor='w')
        ttk.Label(self, textvariable=self.status, padding=(24, 0, 24, 12)).pack(anchor='w')
        for v in self.vars:
            v.trace_add('write', self.changed)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.refresh_assets()
        self.change_theme(mark_dirty=False)
        self.calculate()

    def change_theme(self, mark_dirty=True):
        global BG, INK, BLUE, GREEN, RED
        from themes import apply_theme
        self.palette = apply_theme(self, self.theme_var.get())
        BG, INK, BLUE, GREEN, RED = (self.palette[k] for k in ('bg','ink','accent','positive','negative'))
        if mark_dirty: self.dirty = True
        self.calculate()
        if hasattr(self, 'timeline'): self.timeline.draw()

    def tree(self, parent, columns, widths, height=8):
        box = ttk.Frame(parent)
        box.pack(fill='both', expand=True)
        tree = ttk.Treeview(box, columns=columns, show='headings', height=height, selectmode='browse')
        for c, w in zip(columns, widths):
            tree.heading(c, text=c)
            tree.column(c, width=w, minwidth=65, anchor='w' if c in ('Asset', 'Scenario', 'Type') else 'e')
        y = ttk.Scrollbar(box, orient='vertical', command=tree.yview)
        x = ttk.Scrollbar(box, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        tree.grid(row=0, column=0, sticky='nsew')
        y.grid(row=0, column=1, sticky='ns')
        x.grid(row=1, column=0, sticky='ew')
        box.rowconfigure(0, weight=1)
        box.columnconfigure(0, weight=1)
        return tree

    def build_explore(self):
        controls = ttk.Frame(self.explore, width=350)
        controls.pack(side='left', fill='y', padx=(0, 20))
        controls.pack_propagate(False)
        control_canvas = tk.Canvas(controls, bg=BG, highlightthickness=0, width=325)
        scroll = ttk.Scrollbar(controls, orient='vertical', command=control_canvas.yview)
        control_canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        control_canvas.pack(side='left', fill='both', expand=True)
        left = ttk.Frame(control_canvas)
        window = control_canvas.create_window((0, 0), window=left, anchor='nw')
        left.bind('<Configure>', lambda _: control_canvas.configure(scrollregion=control_canvas.bbox('all')))
        control_canvas.bind('<Configure>', lambda e: control_canvas.itemconfigure(window, width=e.width))
        ttk.Label(left, text='1  Set macro shocks', font=('Helvetica', 16, 'bold')).pack(anchor='w')
        ttk.Label(left, text='Changes from your own baseline.\npp = percentage points.', foreground='#526a80').pack(anchor='w', pady=8)
        self.preset = tk.StringVar(value='No shock')
        combo = ttk.Combobox(left, textvariable=self.preset, values=list(PRESETS), state='readonly', width=29)
        combo.pack(fill='x', pady=(0, 10))
        combo.bind('<<ComboboxSelected>>', self.apply_preset)
        for i, (label, limits) in enumerate(zip(LABELS, LIMITS)):
            ttk.Label(left, text=label).pack(anchor='w', pady=(10, 2))
            row = ttk.Frame(left)
            row.pack(fill='x')
            ttk.Scale(row, variable=self.slider_vars[i], from_=limits[0], to=limits[1], command=lambda x, j=i: self.vars[j].set(f'{float(x):.2f}')).pack(side='left', fill='x', expand=True)
            ttk.Entry(row, textvariable=self.vars[i], width=8).pack(side='right', padx=(8, 0))
            def sync(*_, j=i):
                try: self.slider_vars[j].set(float(self.vars[j].get()))
                except (ValueError, tk.TclError): pass
            self.vars[i].trace_add('write', sync)
        ttk.Button(left, text='Reset shocks to zero', command=lambda: self.set_shocks([0]*len(FACTORS))).pack(fill='x', pady=(20, 8))
        ttk.Button(left, text='Add to comparisons…', command=self.capture).pack(fill='x')
        ttk.Label(left, text='US / euro-area rates, inflation,\nunemployment and GDP are separate.\nAll inputs are changes in percentage points.', foreground='#526a80').pack(anchor='w', pady=14)
        right = ttk.Frame(self.explore)
        right.pack(side='left', fill='both', expand=True)
        ttk.Label(right, text='2  Explore estimated price effects', font=('Helvetica', 16, 'bold')).pack(anchor='w')
        self.validation = tk.StringVar()
        ttk.Label(right, textvariable=self.validation, foreground=RED, wraplength=620).pack(anchor='w', pady=5)
        self.chart = tk.Canvas(right, bg='white', highlightthickness=0, height=370)
        self.chart.pack(fill='x', pady=(4, 12))
        self.chart.bind('<Configure>', lambda _: self.calculate())
        self.results = self.tree(right, ('Asset', 'Total %', *SHORT_LABELS), (200, 85, *([100]*len(FACTORS))))
        ttk.Label(right, text='Largest absolute effects appear first. Total is beside the asset name.\nScroll horizontally for individual rate contributions; Total = their sum.\nOptional custom bond overlays use the selected US or EU rate factor.', foreground='#526a80').pack(anchor='w', pady=8)

    def build_compare(self):
        ttk.Label(self.compare, text='Saved macro scenarios', font=('Helvetica', 16, 'bold')).pack(anchor='w')
        ttk.Label(self.compare, text='All comparisons use the current assets and sensitivities. Up to 12 scenarios.', foreground='#526a80').pack(anchor='w', pady=8)
        row = ttk.Frame(self.compare)
        row.pack(fill='x', pady=(0, 12))
        ttk.Button(row, text='Load selected shocks', command=self.restore).pack(side='left', padx=(0, 8))
        ttk.Button(row, text='Remove selected', command=self.remove_scenario).pack(side='left')
        self.comp = self.tree(self.compare, ('Scenario', *LABELS), (220, *([160]*len(FACTORS))), height=6)
        ttk.Label(self.compare, text='Estimated price changes (%)', font=('Helvetica', 15, 'bold')).pack(anchor='w', pady=(16, 8))
        self.matrix_box = ttk.Frame(self.compare)
        self.matrix_box.pack(fill='both', expand=True)
        self.matrix = None

    def build_assets(self):
        ttk.Label(self.assumptions, text='Configurable scenario sensitivities', font=('Helvetica', 16, 'bold')).pack(anchor='w')
        ttk.Label(self.assumptions, text='Each sensitivity is % price change per +1 percentage-point macro shock.\nCompany names are user labels; adding a ticker does not retrieve or calibrate data.', foreground='#526a80').pack(anchor='w', pady=8)
        row = ttk.Frame(self.assumptions)
        row.pack(fill='x', pady=(0, 12))
        for label, cmd in [('Add company / asset…', lambda: self.edit_asset()), ('Edit selected…', self.edit_selected), ('Remove selected', self.remove_asset)]:
            ttk.Button(row, text=label, command=cmd).pack(side='left', padx=(0, 8))
        self.asset_tree = self.tree(self.assumptions, ('Asset', 'Type', *SHORT_LABELS, 'Duration', 'Convexity', 'Overlay region'), (220, 90, *([90]*len(FACTORS)), 85, 90, 100))
        self.asset_tree.bind('<Double-1>', lambda _: self.edit_selected())
        ttk.Label(self.assumptions, text='Historical bond defaults use yield-based price proxies, not bond-index returns. Extra duration/convexity default to zero.\nOptional overlay: 100 × (−duration × Δyield + ½ × convexity × Δyield²), using the selected US or EU rate.\nNon-bond assets ignore overlays. See Calculations explained for sources and proxy limitations.', foreground='#526a80').pack(anchor='w', pady=14)

    def build_help(self):
        text = tk.Text(self.help, wrap='word', bg='white', fg=INK, padx=24, pady=20, relief='flat', font=('Helvetica', 13))
        scroll = ttk.Scrollbar(self.help, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        text.pack(side='left', fill='both', expand=True)
        from research_notes import METHOD
        text.insert('1.0', 'HOW TO USE THE SIMULATOR\n\nAdjust the thirteen shocks in Scenario lab, add scenarios to Comparisons, and edit coefficients in Assets & sensitivities. The price-effects chart shows the seven core assets plus Sweden, Poland, Norway, Russia and the UK by name. Removing or renaming one leaves N/A rather than substituting another asset. Country map uses real offline boundaries; hover or click countries, drag to pan, and scroll or use buttons to zoom.\n\nSave/load stores timeline points, view and theme in local format 6 sessions (format 5 imports with zero local-rate shocks). CSV export includes assumptions and results. No automatic saving or network access occurs. Earlier session formats are rejected because currency factors were replaced with euro-area unemployment and GDP.\n\n' + METHOD)
        text.configure(state='disabled')

    def changed(self, *_):
        self.dirty = True
        self.calculate()

    def set_shocks(self, values):
        for var, value in zip(self.vars, values): var.set(f'{value:g}')
        self.calculate()

    def apply_preset(self, _=None): self.set_shocks(PRESETS[self.preset.get()])

    def shocks(self): return validate_shocks([v.get() for v in self.vars])

    def calculate(self):
        if not hasattr(self, 'results'): return
        self.results.delete(*self.results.get_children())
        self.chart.delete('all')
        try: shocks = self.shocks()
        except ValueError as e:
            self.validation.set(str(e))
            if hasattr(self, 'explanation'): self.explanation.refresh()
            if hasattr(self, 'country_map'): self.country_map.refresh()
            return
        if hasattr(self, 'explanation'): self.explanation.refresh()
        if hasattr(self, 'country_map'): self.country_map.refresh()
        rows = [(a, *estimate(a, shocks)) for a in self.assets]
        invalid = any(total < -100 for _, _, total in rows)
        self.validation.set('Model breakdown: estimate below −100%; revise shocks or sensitivities.' if invalid else 'Scenario increment • Current asset assumptions • Not a forecast')
        for a, parts, total in sorted(rows, key=lambda row: -abs(row[2])):
            self.results.insert('', 'end', values=(a['name'], f'{total:+.2f}', *(f'{v:+.2f}' for v in parts)))
        w = max(self.chart.winfo_width(), 500)
        h = 370
        visible = chart_results(self.assets, shocks, PRICE_EFFECT_ASSETS)
        extent = max(5, max((abs(value) for _,value in visible if value is not None), default=5)) * 1.15
        label_width=225
        origin=label_width+(w-label_width)/2
        scale=max(30,w-label_width-80)/(2*extent)
        self.chart.create_line(origin,24,origin,h-16,fill=self.palette['grid'])
        self.chart.create_text(12,12,anchor='w',text='Estimated price increment (%) · core assets + added markets',fill=self.palette['muted'])
        for i,(name,total) in enumerate(visible):
            y=36+i*27
            self.chart.create_text(12,y+5,anchor='w',text=name,fill=INK,font=('Helvetica',11))
            if total is None:
                self.chart.create_text(origin,y+5,text='N/A — asset missing',fill=self.palette['muted']);continue
            end=origin+total*scale
            color=GREEN if total>0 else RED if total<0 else self.palette['grid']
            self.chart.create_rectangle(min(origin,end),y-3,max(origin,end)+1,y+13,fill=color,outline='')
            self.chart.create_text(end+(5 if total>=0 else -5),y+5,anchor='w' if total>=0 else 'e',text=f'{total:+.1f}',fill=INK)

    def refresh_assets(self):
        self.asset_tree.delete(*self.asset_tree.get_children())
        for i, a in enumerate(self.assets):
            self.asset_tree.insert('', 'end', iid=str(i), values=(a['name'], a['kind'], *(f'{v:.2f}' for v in a['sens']), a['duration'], a['convexity'], a['rate_region']))
        self.refresh_compare()
        if hasattr(self, 'timeline'): self.timeline.refresh()
        self.calculate()

    def selected(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo('Select a row', 'Select a row first.', parent=self)
            return None
        return int(selected[0])

    def edit_selected(self):
        index = self.selected(self.asset_tree)
        if index is not None: self.edit_asset(index)

    def edit_asset(self, index=None):
        if index is None and len(self.assets) >= 100:
            messagebox.showerror('Asset limit', 'At most 100 assets are supported.'); return
        a = self.assets[index] if index is not None else dict(name='', kind='Company', sens=[0]*len(FACTORS), duration=0, convexity=0, rate_region='US')
        dialog = tk.Toplevel(self)
        dialog.title('Edit illustrative asset assumptions')
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry('660x650')
        canvas=tk.Canvas(dialog, highlightthickness=0, bg=self.palette['bg'])
        scroll=ttk.Scrollbar(dialog, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True)
        body = ttk.Frame(canvas, padding=24)
        window=canvas.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda _:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
        fields = []
        labels = ['Name / ticker', 'Type', *LABELS, 'Extra duration (years)', 'Extra convexity', 'Overlay rate region']
        values = [a['name'], a['kind'], *(f'{v:.2f}' for v in a['sens']), a['duration'], a['convexity'], a['rate_region']]
        for i, (label, value) in enumerate(zip(labels, values)):
            ttk.Label(body, text=label).grid(row=i, column=0, sticky='w', padx=(0, 20), pady=5)
            v = tk.StringVar(value=str(value)); fields.append(v)
            widget = ttk.Combobox(body, textvariable=v, values=['Equity', 'Bond', 'Company'], state='readonly') if i == 1 else ttk.Entry(body, textvariable=v, width=28)
            if i == 4+len(FACTORS): widget = ttk.Combobox(body, textvariable=v, values=['US', 'EU'], state='readonly')
            widget.grid(row=i, column=1, sticky='ew')
        ttk.Label(body, text='Sensitivities are rounded to 2 decimal places when saved.\nNew assets start with zero exposure; configure explicitly.', foreground=RED).grid(row=5+len(FACTORS), column=0, columnspan=2, pady=12)
        def commit():
            try:
                candidate = validate_asset(dict(name=fields[0].get(), kind=fields[1].get(), sens=[v.get() for v in fields[2:2+len(FACTORS)]], duration=fields[2+len(FACTORS)].get(), convexity=fields[3+len(FACTORS)].get(), rate_region=fields[4+len(FACTORS)].get()))
                if any(other['name'].casefold() == candidate['name'].casefold() for j, other in enumerate(self.assets) if j != index):
                    raise ValueError('Use a unique asset name.')
            except ValueError as e:
                messagebox.showerror('Check assumptions', str(e), parent=dialog); return
            if index is None: self.assets.append(candidate)
            else: self.assets[index] = candidate
            self.dirty = True
            self.refresh_assets()
            dialog.destroy()
        ttk.Button(body, text='Save assumptions', command=commit).grid(row=6+len(FACTORS), column=1, sticky='e')
        ttk.Button(body, text='Cancel', command=dialog.destroy).grid(row=6+len(FACTORS), column=0, sticky='w')

    def remove_asset(self):
        i = self.selected(self.asset_tree)
        if i is None: return
        if len(self.assets) == 1:
            messagebox.showinfo('Keep one asset', 'At least one asset is required.'); return
        if messagebox.askyesno('Remove asset', f'Remove {self.assets[i]["name"]}?'):
            self.assets.pop(i); self.dirty = True; self.refresh_assets()

    def capture(self):
        try: shocks = self.shocks()
        except ValueError as e: messagebox.showerror('Check shocks', str(e)); return
        if len(self.scenarios) >= 12:
            messagebox.showinfo('Comparison limit', 'Remove a comparison before adding another.'); return
        name = simpledialog.askstring('Name scenario', 'Comparison name:', initialvalue=f'Scenario {len(self.scenarios)+1}', parent=self)
        if name is None: return
        if not 1 <= len(name.strip()) <= 80:
            messagebox.showerror('Name required', 'Use 1–80 characters.'); return
        self.scenarios.append(dict(name=name.strip(), shocks=shocks))
        self.dirty = True; self.refresh_compare(); self.timeline.refresh(); self.tabs.select(self.compare)

    def refresh_compare(self):
        self.comp.delete(*self.comp.get_children())
        for i, s in enumerate(self.scenarios): self.comp.insert('', 'end', iid=str(i), values=(s['name'], *s['shocks']))
        for child in self.matrix_box.winfo_children(): child.destroy()
        columns = ('Asset', *(f'{i+1}: {s["name"]}' for i, s in enumerate(self.scenarios)))
        self.matrix = self.tree(self.matrix_box, columns, (220, *([150]*len(self.scenarios))), height=8)
        for a in self.assets:
            self.matrix.insert('', 'end', values=(a['name'], *(f'{estimate(a, s["shocks"])[1]:+.2f}' for s in self.scenarios)))

    def restore(self):
        i = self.selected(self.comp)
        if i is not None: self.set_shocks(self.scenarios[i]['shocks']); self.tabs.select(self.explore)

    def remove_scenario(self):
        i = self.selected(self.comp)
        if i is not None: self.scenarios.pop(i); self.dirty = True; self.refresh_compare(); self.timeline.refresh()

    def session(self):
        return validate_session(dict(version=6, shocks=self.shocks(), assets=self.assets, scenarios=self.scenarios, timeline=self.timeline_points, theme=self.theme_var.get(), timeline_mode=self.timeline.mode.get()))

    def save(self):
        try: data = self.session()
        except ValueError as e: messagebox.showerror('Check inputs', str(e)); return False
        path = filedialog.asksaveasfilename(title='Save local session', initialfile='macro-session.json', defaultextension='.json', filetypes=[('Session JSON', '*.json')])
        if not path: return False
        temp = None
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=Path(path).parent, delete=False) as f:
                temp = f.name; json.dump(data, f, indent=2, allow_nan=False)
            os.replace(temp, path)
        except OSError as e:
            if temp and os.path.exists(temp): os.unlink(temp)
            messagebox.showerror('Cannot save', str(e)); return False
        self.dirty = False; self.filepath = path; self.status.set(f'Saved locally: {Path(path).name}'); return True

    def may_discard(self):
        if not self.dirty: return True
        choice = messagebox.askyesnocancel('Unsaved changes', 'Save your session before continuing?')
        return False if choice is None else self.save() if choice else True

    def load(self):
        if not self.may_discard(): return
        path = filedialog.askopenfilename(title='Load local session', filetypes=[('Session JSON', '*.json')])
        if not path: return
        try:
            if Path(path).stat().st_size > 2_000_000: raise ValueError('Session file is too large (maximum 2 MB).')
            data = validate_session(json.loads(Path(path).read_text(encoding='utf-8')))
        except (OSError, ValueError, TypeError, KeyError, RecursionError) as e:
            messagebox.showerror('Cannot load session', str(e)); return
        self.assets = data['assets']; self.scenarios = data['scenarios']; self.timeline_points = data['timeline']
        self.timeline.editing = None
        self.timeline.mode.set(data['timeline_mode']); self.theme_var.set(data['theme']); self.change_theme(mark_dirty=False)
        self.set_shocks(data['shocks'])
        self.refresh_assets(); self.dirty = False; self.filepath = path; self.status.set(f'Loaded locally: {Path(path).name}')

    def export(self):
        try: current = self.shocks()
        except ValueError as e: messagebox.showerror('Check inputs', str(e)); return
        path = filedialog.asksaveasfilename(title='Export illustrative results', initialfile='macro-results.csv', defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if not path: return
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Scenario increments; rounded empirical magnitudes with negative stock rate sign overrides; not causal forecasts; bond yield proxies'])
                writer.writerow(['Scenario', 'Asset', 'Type', *LABELS, *[k+' sensitivity' for k in FACTORS], 'Duration', 'Convexity', 'Overlay rate region', *[k+' contribution %' for k in FACTORS], 'Estimated price change %', 'Below -100%'])
                def safe(s): return "'" + s if s.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else s
                for s in [dict(name='Current', shocks=current), *self.scenarios]:
                    for a in self.assets:
                        parts, total = estimate(a, s['shocks'])
                        writer.writerow([safe(s['name']), safe(a['name']), a['kind'], *s['shocks'], *a['sens'], a['duration'], a['convexity'], a['rate_region'], *parts, total, total < -100])
        except OSError as e: messagebox.showerror('Cannot export', str(e)); return
        self.status.set(f'Exported locally: {Path(path).name}')

    def close(self):
        if self.may_discard(): self.destroy()

if __name__ == '__main__':
    App().mainloop()
