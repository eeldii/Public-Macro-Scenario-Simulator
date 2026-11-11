"""Offline quarterly timeline editor and interactive line chart."""
import copy
import csv
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from model import CHART_ASSETS, LABELS, estimate
from timeline_model import MODES, quarter_index, quarter_label, validate_timeline, fill_gaps, series_for
from themes import palette_for

COLORS=('#4388e8','#e39535','#2caf9a','#a879dc','#db6b85','#7f9d34','#35a4c4')

class Timeline(ttk.Frame):
    def __init__(self,parent,app):
        super().__init__(parent,padding=16)
        self.app=app;self.hover_points=[];self.editing=None
        ttk.Label(self,text='Scenario timeline',font=('Helvetica',18,'bold')).pack(anchor='w')
        ttk.Label(self,text='Assign a scenario to a quarter, then compare asset effects over time. Dated points store shock snapshots.').pack(anchor='w',pady=5)
        row=ttk.Frame(self);row.pack(fill='x',pady=6)
        today=date.today()
        self.year=tk.StringVar(value=str(today.year));self.quarter=tk.StringVar(value='Q'+str((today.month-1)//3+1))
        self.source=tk.StringVar(value='Current scenario lab');self.name=tk.StringVar(value='')
        for text in ('Year',):ttk.Label(row,text=text).pack(side='left')
        ttk.Spinbox(row,from_=1900,to=2200,textvariable=self.year,width=6).pack(side='left',padx=6)
        ttk.Combobox(row,textvariable=self.quarter,values=['Q1','Q2','Q3','Q4'],state='readonly',width=4).pack(side='left')
        self.source_box=ttk.Combobox(row,textvariable=self.source,state='readonly',width=28)
        self.source_box.pack(side='left',padx=8)
        ttk.Entry(row,textvariable=self.name,width=20).pack(side='left')
        ttk.Button(row,text='Add point',command=self.add).pack(side='left',padx=6)
        ttk.Button(row,text='Update selected',command=lambda:self.add(update=True)).pack(side='left')
        self.table=app.tree(self,('Quarter','Scenario',*LABELS),(110,220,*([145]*len(LABELS))),height=2)
        self.table.bind('<<TreeviewSelect>>',self.select)
        controls=ttk.Frame(self);controls.pack(fill='x',pady=8)
        ttk.Button(controls,text='Remove selected',command=self.remove).pack(side='left')
        ttk.Button(controls,text='Load point into lab',command=self.restore).pack(side='left',padx=6)
        ttk.Button(controls,text='Fill missing quarters with zero change',command=self.fill).pack(side='left')
        ttk.Button(controls,text='Export timeline CSV…',command=self.export).pack(side='left',padx=6)
        self.mode=tk.StringVar(value=MODES[0])
        viewrow=ttk.Frame(self);viewrow.pack(fill='x',pady=(0,6))
        ttk.Label(viewrow,text='Graph view:  ').pack(side='left')
        mode_box=ttk.Combobox(viewrow,textvariable=self.mode,values=MODES,state='readonly',width=29)
        mode_box.pack(side='left');mode_box.bind('<<ComboboxSelected>>',self.change_mode)
        toggles=ttk.Frame(self);toggles.pack(fill='x')
        self.enabled={}
        for i,name in enumerate(CHART_ASSETS):
            value=tk.BooleanVar(value=name in ('US stocks','EUR stocks average','US government bonds'))
            self.enabled[name]=value
            cell=ttk.Frame(toggles);cell.grid(row=i//4,column=i%4,sticky='w',padx=(0,12))
            tk.Label(cell,text='●',fg=COLORS[i],bg=palette_for(app)['bg']).pack(side='left')
            ttk.Checkbutton(cell,text=name,variable=value,command=self.draw).pack(side='left')
        self.canvas=tk.Canvas(self,height=260,bg='white',highlightthickness=0)
        self.canvas.pack(fill='both',expand=True,pady=8)
        self.canvas.bind('<Configure>',lambda _:self.draw())
        self.canvas.bind('<Motion>',self.hover)
        self.canvas.bind('<Leave>',lambda _:self.info.set('Hover over a chart point for the quarter, scenario and result.'))
        self.info=tk.StringVar(value='Hover over a chart point for the quarter, scenario and result.')
        ttk.Label(self,textvariable=self.info).pack(anchor='w')
        self.note=tk.StringVar()
        ttk.Label(self,textvariable=self.note,wraplength=1120).pack(anchor='w',pady=6)

    def change_mode(self, _=None):
        self.app.dirty=True
        self.refresh()

    def sources(self):
        return ['Current scenario lab',*[f'{i+1}: {s["name"]}' for i,s in enumerate(self.app.scenarios)]]

    def point_shocks(self):
        if self.source.get()=='Selected point snapshot' and self.editing is not None:
            return copy.deepcopy(self.app.timeline_points[self.editing]['shocks'])
        if self.source.get()=='Current scenario lab':return self.app.shocks()
        choices=self.sources()
        if self.source.get() not in choices:raise ValueError('Choose a scenario source.')
        return copy.deepcopy(self.app.scenarios[choices.index(self.source.get())-1]['shocks'])

    def add(self,update=False):
        try:
            if update and self.editing is None:raise ValueError('Select a timeline row to update.')
            point=dict(quarter=f'{self.year.get()}-{self.quarter.get()}',name=self.name.get().strip() or self.source.get(),shocks=self.point_shocks())
            points=copy.deepcopy(self.app.timeline_points)
            if update:points[self.editing]=point
            else:points.append(point)
            self.app.timeline_points=validate_timeline(points)
        except (ValueError,IndexError) as error:messagebox.showerror('Check timeline',str(error),parent=self);return
        self.app.dirty=True;self.editing=None;self.source.set('Current scenario lab');self.refresh()

    def select(self,_=None):
        selection=self.table.selection()
        if not selection:return
        self.editing=int(selection[0]);point=self.app.timeline_points[self.editing]
        self.year.set(point['quarter'][:4]);self.quarter.set(point['quarter'][5:]);self.name.set(point['name'])
        self.source_box.configure(values=[*self.sources(),'Selected point snapshot']);self.source.set('Selected point snapshot')

    def remove(self):
        if self.editing is None:return
        self.app.timeline_points.pop(self.editing);self.editing=None;self.app.dirty=True;self.refresh()

    def restore(self):
        if self.editing is not None:
            self.app.set_shocks(self.app.timeline_points[self.editing]['shocks']);self.app.tabs.select(self.app.explore)

    def fill(self):
        try:self.app.timeline_points=fill_gaps(self.app.timeline_points)
        except ValueError as error:messagebox.showerror('Cannot fill gaps',str(error),parent=self);return
        self.app.dirty=True;self.editing=None;self.refresh()

    def refresh(self):
        values=self.sources()
        if self.editing is not None:values.append('Selected point snapshot')
        self.source_box.configure(values=values)
        if self.source.get() not in values:self.source.set(values[0])
        self.table.delete(*self.table.get_children())
        for i,point in enumerate(self.app.timeline_points):self.table.insert('','end',iid=str(i),values=(point['quarter'],point['name'],*point['shocks']))
        self.draw()

    def draw(self):
        if not hasattr(self,'canvas'):return
        p=palette_for(self.app);self.canvas.configure(bg=p['surface']);self.canvas.delete('all');self.hover_points=[]
        points=self.app.timeline_points
        self.note.set('Common baseline: effects are independent dated scenarios. Lines join assigned points only; gaps are not estimated. No drift, income or forecast is included.' if self.mode.get()==MODES[0] else 'Hypothetical index: treats scenario increments as if quarterly price returns and compounds from 100. Every quarter must be assigned. Excludes baseline returns, dividends/coupons and fees; not a forecast.')
        if not points:
            self.canvas.create_text(24,35,anchor='nw',text='Add your first dated scenario above, for example 2026-Q4.',fill=p['muted']);return
        assets={a['name']:a for a in self.app.assets};series=[]
        try:
            for i,name in enumerate(CHART_ASSETS):
                if self.enabled[name].get() and name in assets:series.append((name,COLORS[i],series_for(assets[name],points,self.mode.get())))
        except ValueError as error:
            self.canvas.create_text(24,35,anchor='nw',width=max(250,self.canvas.winfo_width()-48),text=str(error),fill=p['negative']);return
        if not series:
            self.canvas.create_text(24,35,anchor='nw',text='Select at least one available asset above.',fill=p['muted']);return
        w=max(500,self.canvas.winfo_width());h=max(100,self.canvas.winfo_height());left,right,top,bottom=70,w-25,28,h-42
        values=[v for _,_,rows in series for _,v,_ in rows]
        low,high=min(values),max(values);pad=max((high-low)*0.12,1);low-=pad;high+=pad
        first,last=quarter_index(series[0][2][0][0],allow_baseline=True),quarter_index(points[-1]['quarter'])
        def xy(q,v):return left+(quarter_index(q,allow_baseline=True)-first)/(last-first)*(right-left),bottom-(v-low)/(high-low)*(bottom-top)
        for i in range(5):
            value=low+(high-low)*i/4;y=xy(quarter_label(first),value)[1]
            self.canvas.create_line(left,y,right,y,fill=p['grid'])
            self.canvas.create_text(left-8,y,anchor='e',text=f'{value:.1f}',fill=p['muted'])
        ticks=sorted({first,last,*range(first,last+1,max(1,(last-first)//7))})
        for q in ticks:
            x=xy(quarter_label(q),low)[0]
            self.canvas.create_text(x,bottom+18,text=quarter_label(q),fill=p['muted'],font=('Helvetica',10))
        for name,color,rows in series:
            previous=None
            for q,value,scenario in rows:
                x,y=xy(q,value)
                if previous:
                    px,py,pq=previous
                    self.canvas.create_line(px,py,x,y,fill=color,width=2,dash=(5,4) if quarter_index(q,allow_baseline=True)-quarter_index(pq,allow_baseline=True)>1 else ())
                self.canvas.create_oval(x-4,y-4,x+4,y+4,fill=color,outline=p['surface'])
                self.hover_points.append((x,y,f'{q} · {scenario} · {name}: {value:+.2f}%' if self.mode.get()==MODES[0] else f'{q} · {scenario} · {name}: index {value:.2f}'))
                previous=x,y,q
        self.canvas.create_text(left,12,anchor='w',text='Price effect (%)' if self.mode.get()==MODES[0] else 'Hypothetical index · initial value 100',fill=p['ink'])
        # Match series colours to the asset switches without changing semantic colours elsewhere.
        self.info.set('Hover over a chart point for the quarter, scenario and result.')

    def hover(self,event):
        if not self.hover_points:return
        point=min(self.hover_points,key=lambda p:(p[0]-event.x)**2+(p[1]-event.y)**2)
        if (point[0]-event.x)**2+(point[1]-event.y)**2<225:self.info.set(point[2])

    def export(self):
        try:
            rows=[]
            for asset in self.app.assets:
                for quarter,value,scenario in series_for(asset,self.app.timeline_points,self.mode.get()):rows.append([quarter,scenario,asset['name'],self.mode.get(),value])
        except ValueError as error:messagebox.showerror('Cannot export',str(error),parent=self);return
        path=filedialog.asksaveasfilename(defaultextension='.csv',initialfile='macro-timeline.csv',filetypes=[('CSV','*.csv')])
        if not path:return
        def safe(value):return "'"+value if isinstance(value,str) and value.startswith(('=','+','-','@','\t','\r','\n')) else value
        try:
            with open(path,'w',newline='',encoding='utf-8') as f:
                writer=csv.writer(f);writer.writerow(['Quarter','Scenario','Asset','View','Value']);writer.writerows([[safe(v) for v in row] for row in rows])
        except OSError as error:messagebox.showerror('Cannot export',str(error),parent=self)
