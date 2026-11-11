"""Offline explanation and interactive country map panels."""
import tkinter as tk
from tkinter import ttk
from countries import COUNTRIES, PROXY_COUNTRIES, asset_name, effect_color
from model import FACTORS, LABELS, SHORT_LABELS, estimate
from themes import palette_for

def tooltip_position(x, y, width, height, canvas_width, canvas_height):
    left = x + 16 if x + 16 + width <= canvas_width else x - width - 16
    top = y + 18 if y + 18 + height <= canvas_height else y - height - 18
    return max(4, min(left, max(4, canvas_width-width-4))), max(4, min(top, max(4, canvas_height-height-4)))

class Explanation(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=16)
        self.app = app
        ttk.Label(self, text='Where do the numbers come from?', font=('Helvetica', 18, 'bold')).pack(anchor='w')
        ttk.Label(self, text='Choose an asset to inspect its current assumptions and calculation.').pack(anchor='w', pady=8)
        self.choice = ttk.Combobox(self, state='readonly', width=44)
        self.choice.pack(anchor='w')
        self.choice.bind('<<ComboboxSelected>>', lambda _: self.refresh())
        frame = ttk.Frame(self)
        frame.pack(fill='both', expand=True, pady=(12, 0))
        self.text = tk.Text(frame, wrap='word', bg='white', fg='#142c45', relief='flat', padx=20, pady=16, font=('Helvetica', 13))
        scroll = ttk.Scrollbar(frame, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

    def refresh(self):
        names = [a['name'] for a in self.app.assets]
        self.choice.configure(values=names)
        if self.choice.get() not in names: self.choice.set(names[0])
        a = next(a for a in self.app.assets if a['name'] == self.choice.get())
        from research_notes import METHOD, provenance_text
        body = provenance_text(a) + '\nCURRENT SHOCK CALCULATION: ' + a['name'] + '\n\n'
        try:
            shocks = self.app.shocks()
            parts, total = estimate(a, shocks)
            for label, sensitivity, shock, contribution in zip(LABELS, a['sens'], shocks, parts):
                body += f'{label}\n  Assumption {sensitivity:+.2f} × shock {shock:+g}'
                if a['kind'] == 'Bond' and label == LABELS[0 if a['rate_region']=='US' else 1] and (a['duration'] or a['convexity']):
                    dy = shocks[0 if a['rate_region']=='US' else 1] / 100
                    overlay = sensitivity * shock
                    bond = 100 * (-a['duration'] * dy + 0.5*a['convexity']*dy*dy)
                    body += f' = overlay {overlay:+.3f}%\n  Duration {a["duration"]:g}; convexity {a["convexity"]:g}; Δyield {dy:g}\n  100 × (−duration × Δyield + ½ × convexity × Δyield²) = {bond:+.3f}%'
                body += f'\n  Contribution: {contribution:+.3f} percentage points\n\n'
            body += f'TOTAL ESTIMATED PRICE CHANGE: {total:+.3f}%\nSum of the contributions above; not annualized.\n'
            if total < -100: body += '\nMODEL BREAKDOWN: below −100%; not a valid simple long-position return.\n'
        except ValueError:
            body += 'Correct the invalid shocks in Scenario lab to see the calculation.\n'
        body += '\n\n' + METHOD
        self.text.configure(state='normal')
        self.text.delete('1.0', 'end'); self.text.insert('1.0', body)
        self.text.configure(state='disabled')

class CountryMap(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=16)
        self.app = app
        from map_geometry import load_boundaries
        self.boundaries = load_boundaries()
        self.zoom = 1.0
        self.pan = [0, 0]
        self.drag_anchor = None
        self.selected = COUNTRIES[0][1]
        ttk.Label(self, text='US and European market impact map', font=('Helvetica', 18, 'bold')).pack(anchor='w')
        ttk.Label(self, text='Natural Earth country boundaries • Stock-price effects, not national welfare • Drag to pan / scroll to zoom').pack(anchor='w', pady=6)
        ttk.Label(self, text='Red: negative | Grey: zero | Green: positive | Blue-grey: no model | New markets + Latvia/Lithuania: proxies | Colour caps at ±10%; square-root contrast highlights small changes').pack(anchor='w')
        row = ttk.Frame(self); row.pack(fill='x', pady=8)
        self.choice = ttk.Combobox(row, state='readonly', values=[c[1] for c in COUNTRIES], width=24)
        self.choice.set(self.selected); self.choice.pack(side='left')
        self.choice.bind('<<ComboboxSelected>>', lambda _: self.select(self.choice.get()))
        ttk.Button(row, text='Edit country assumptions…', command=self.edit).pack(side='left', padx=12)
        for label, command in [('−', lambda: self.change_zoom(0.8)), ('+', lambda: self.change_zoom(1.25)), ('Reset map', self.reset_view)]:
            ttk.Button(row, text=label, command=command).pack(side='left', padx=3)
        self.canvas = tk.Canvas(self, bg='#eaf1f8', highlightthickness=0, height=320)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda _: self.refresh())
        self.canvas.bind('<MouseWheel>', lambda e: self.change_zoom(1.12 if e.delta > 0 else 1/1.12))
        self.canvas.bind('<ButtonPress-1>', lambda e: setattr(self, 'drag_anchor', (e.x, e.y)))
        self.canvas.bind('<B1-Motion>', self.drag)
        self.info = tk.StringVar()
        tk.Label(self, textvariable=self.info, wraplength=940, justify='left', anchor='nw', height=5, bg='#f3f6fa', fg='#142c45').pack(anchor='w', fill='x', pady=12)
        self._hover_country = None
        self._tooltip = tk.Label(self.canvas, bg='#142c45', fg='white', justify='left', anchor='nw', padx=12, pady=10, font=('Helvetica', 11), relief='solid', borderwidth=1)
        self.canvas.bind('<Leave>', lambda _: self.hide_tooltip())
        self._build_scene()

    def select(self, country):
        self.selected = country; self.choice.set(country); self.refresh()

    def edit(self):
        target = asset_name(self.selected)
        for i, a in enumerate(self.app.assets):
            if a['name'] == target:
                self.app.edit_asset(i); return
        from tkinter import messagebox
        messagebox.showinfo('Country asset missing', f'Add an equity asset named “{target}” to enable this country. Renaming or removing its linked asset makes the country unavailable.')

    def _build_scene(self):
        """Create and bind once. Never delete the item dispatching a mouse event.

        Recreating a hovered/clicked item in its own callback can re-enter native
        Tk canvas pointer dispatch on macOS. Selection only changes styling.
        """
        self._polygons = []
        self._labels = []
        self._scene_items = []
        self._last_transform = None
        selected_codes = {c[0]: c[1] for c in COUNTRIES}
        for feature in self.boundaries:
            country = selected_codes.get(feature['iso'])
            tag = 'country_' + feature['iso']
            for ring in feature['rings']:
                item = self.canvas.create_polygon(0, 0, 0, 0, 0, 0, tags=(tag,))
                self._polygons.append((item, ring, country))
                self._scene_items.append(item)
            if country:
                self.canvas.tag_bind(tag, '<Button-1>', lambda _, c=country: self.select(c))
                self.canvas.tag_bind(tag, '<Enter>', lambda e, c=country: self.hover(c, e))
            else:
                self.canvas.tag_bind(tag, '<Enter>', lambda e, n=feature['name']: self.hover(n, e))
            self.canvas.tag_bind(tag, '<Motion>', lambda e: self.move_tooltip(e))
            self.canvas.tag_bind(tag, '<Leave>', lambda _: self.leave_country())
        for code, country, lon, lat in COUNTRIES:
            tag = 'label_' + code
            item = self.canvas.create_text(0, 0, text=code, fill='#102c39', font=('Helvetica', 10, 'bold'), tags=(tag,))
            self._labels.append((item, lon, lat, country))
            self._scene_items.append(item)
            self.canvas.tag_bind(tag, '<Button-1>', lambda _, c=country: self.select(c))
            self.canvas.tag_bind(tag, '<Enter>', lambda e, c=country: self.hover(c, e))
            self.canvas.tag_bind(tag, '<Motion>', lambda e: self.move_tooltip(e))
            self.canvas.tag_bind(tag, '<Leave>', lambda _: self.leave_country())
        self._north = self.canvas.create_text(12, 12, anchor='nw', text='N ↑   Northern markets · Mercator', fill='#526a80')
        self._credit = self.canvas.create_text(0, 0, anchor='se', text='Natural Earth · public domain', fill='#526a80')
        self._scene_items.extend((self._north, self._credit))
        self._error = self.canvas.create_text(25, 25, anchor='nw', text='Correct the scenario inputs to display country effects.', state='hidden')

    def refresh(self):
        if not hasattr(self, '_scene_items'):
            return
        try:
            shocks = self.app.shocks()
        except ValueError:
            self.hide_tooltip()
            for item in self._scene_items: self.canvas.itemconfigure(item, state='hidden')
            self.canvas.itemconfigure(self._error, state='normal')
            self.info.set('Map unavailable while scenario inputs are invalid.')
            return
        self.canvas.itemconfigure(self._error, state='hidden')
        for item in self._scene_items: self.canvas.itemconfigure(item, state='normal')
        assets = {a['name']: a for a in self.app.assets}
        palette = palette_for(self.app)
        from map_geometry import viewport, project
        width, height = max(self.canvas.winfo_width(), 300), max(self.canvas.winfo_height(), 200)
        scale, ox, oy = viewport(width, height)
        scale *= self.zoom
        ox = width/2 + (ox-width/2)*self.zoom + self.pan[0]
        oy = height/2 + (oy-height/2)*self.zoom + self.pan[1]
        transform = (scale, ox, oy)
        values = {name: estimate(a, shocks)[1] for name, a in assets.items()}
        for item, ring, country in self._polygons:
            if transform != self._last_transform:
                self.canvas.coords(item, *[v for x, y in ring for v in (ox+x*scale, oy+y*scale)])
            value = values.get(asset_name(country)) if country else None
            self.canvas.itemconfigure(item, fill=effect_color(value) if value is not None else palette['grid'], outline=palette['accent'] if country == self.selected else palette['surface'], width=2 if country == self.selected else 1)
        if transform != self._last_transform:
            for item, lon, lat, country in self._labels:
                x, y = project(lon, lat)
                self.canvas.coords(item, ox+x*scale, oy+y*scale)
            self.canvas.coords(self._credit, width-12, height-10)
            self._last_transform = transform
        for item, _, _, country in self._labels:
            self.canvas.itemconfigure(item, fill='#102c39' if asset_name(country) in assets else palette['ink'])
        self.canvas.itemconfigure(self._north, fill=palette['muted'])
        self.canvas.itemconfigure(self._credit, fill=palette['muted'])
        self.detail(self.selected)
        if self.__dict__.get('_hover_country') and self.__dict__.get('_tooltip') is not None:
            self._tooltip.configure(text=self.tooltip_text(self._hover_country))

    def change_zoom(self, factor):
        self.hide_tooltip()
        self.zoom=max(1,min(5,self.zoom*factor));self.refresh()

    def reset_view(self):
        self.hide_tooltip()
        self.zoom=1;self.pan=[0,0];self.refresh()

    def drag(self, event):
        self.hide_tooltip()
        if self.drag_anchor:
            self.pan[0]+=event.x-self.drag_anchor[0]
            self.pan[1]+=event.y-self.drag_anchor[1]
            self.drag_anchor=(event.x,event.y)
            self.refresh()

    def hide_tooltip(self):
        self._hover_country = None
        if self.__dict__.get('_tooltip') is not None: self._tooltip.place_forget()

    def leave_country(self):
        self.hide_tooltip()
        self.detail(self.selected)

    def hover(self, country, event=None):
        self._hover_country = country
        self.detail(country)
        if event is not None: self.move_tooltip(event)

    def tooltip_text(self, country):
        asset = next((a for a in self.app.assets if a['name'] == asset_name(country)), None)
        if asset is None: return country + '\nNo modeled result (asset missing or country unmodeled).'
        try: parts, total = estimate(asset, self.app.shocks())
        except ValueError: return country + '\nCorrect the invalid scenario inputs.'
        from model import SHORT_LABELS
        text = f'{country}  {total:+.2f}%\nEstimated stock-price change\n\n'
        text += '\n'.join(f'{label}: {value:+.2f} pp' for label, value in zip(SHORT_LABELS, parts))
        if country in PROXY_COUNTRIES: text += '\nEuro-area proxy; local rates are assumed'
        if total < -100: text += '\nModel breakdown: below −100%'
        return text

    def move_tooltip(self, event):
        if not self._hover_country or self.__dict__.get('_tooltip') is None: return
        self._tooltip.configure(text=self.tooltip_text(self._hover_country))
        width, height = self._tooltip.winfo_reqwidth(), self._tooltip.winfo_reqheight()
        x, y = tooltip_position(event.x, event.y, width, height, self.canvas.winfo_width(), self.canvas.winfo_height())
        self._tooltip.place(x=x, y=y)
        self._tooltip.lift()


    def detail(self, country):
        a = next((a for a in self.app.assets if a['name'] == asset_name(country)), None)
        if not a:
            self.info.set(f'{country}: N/A — linked asset removed or renamed.'); return
        try: parts, total = estimate(a, self.app.shocks())
        except ValueError: self.info.set('Correct the invalid scenario inputs.'); return
        from model import PROVENANCE, default_status
        label = 'Euro-area proxy; local rates are assumed, not a country-specific fit' if country in PROXY_COUNTRIES else 'Research-informed or edited assumptions'
        if not default_status(a): label = 'Custom assumptions'
        self.info.set(f'{country}: {total:+.2f}% estimated stock-price increment. {label}.\n' + '  |  '.join(f'{factor}: {part:+.2f}' for factor, part in zip(SHORT_LABELS, parts)) + ('\nBelow −100%: model breakdown.' if total < -100 else '') + '\nClick a country to select; edit assumptions to change its model. US and euro-area rates, inflation, unemployment and GDP are separate.')
