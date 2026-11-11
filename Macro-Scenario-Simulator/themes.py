"""Offline application palettes and shared Tk/ttk styling."""
THEMES = {
 'Forest': dict(bg='#edf3ed',surface='#fbfdf7',ink='#213c30',muted='#547563',accent='#2b785c',positive='#167c51',negative='#b44b52',grid='#abc2b3',sea='#deebe7'),
}

def palette_for(app):
    return getattr(app,'palette',THEMES['Forest'])

def apply_theme(root, name):
    from tkinter import ttk
    palette=THEMES[name]
    style=ttk.Style(root)
    style.configure('.',background=palette['bg'],foreground=palette['ink'])
    for widget in ('TFrame','TLabel','TNotebook','TLabelframe','TLabelframe.Label','TCheckbutton'):
        style.configure(widget,background=palette['bg'],foreground=palette['ink'])
    style.configure('TButton',background=palette['surface'],foreground=palette['ink'])
    style.map('TButton',background=[('active',palette['grid'])])
    style.configure('TNotebook.Tab',background=palette['bg'],foreground=palette['muted'])
    style.map('TNotebook.Tab',background=[('selected',palette['surface'])],foreground=[('selected',palette['ink'])])
    for widget in ('TEntry','TCombobox','TSpinbox'):
        style.configure(widget,fieldbackground=palette['surface'],foreground=palette['ink'],background=palette['surface'],insertcolor=palette['ink'])
        style.map(widget,fieldbackground=[('readonly',palette['surface'])],foreground=[('readonly',palette['ink'])],selectbackground=[('!disabled',palette['accent'])],selectforeground=[('!disabled',palette['bg'])])
    style.configure('Treeview',background=palette['surface'],fieldbackground=palette['surface'],foreground=palette['ink'])
    style.configure('Treeview.Heading',background=palette['bg'],foreground=palette['ink'])
    style.map('Treeview',background=[('selected',palette['accent'])],foreground=[('selected',palette['bg'])])
    root.option_add('*TCombobox*Listbox.background',palette['surface'])
    root.option_add('*TCombobox*Listbox.foreground',palette['ink'])
    # Explicit colours on existing plain widgets and labels must follow the theme too.
    roles={'#f3f6fa':'bg','#ffffff':'surface','#142c45':'ink','#526a80':'muted','#2864c5':'accent','#17836c':'positive','#c04b58':'negative','#b4c3d1':'grid','#eaf1f8':'sea'}
    for values in THEMES.values():
        for key,value in values.items():roles.setdefault(value,key)
    def walk(widget):
        keys=widget.keys()
        for option in ('background','foreground','insertbackground'):
            if option not in keys:continue
            try:
                old=str(widget.cget(option))
                role=roles.get(old)
                if role:widget.configure(**{option:palette[role]})
            except Exception:pass
        for child in widget.winfo_children():walk(child)
    walk(root)
    root.configure(bg=palette['bg'])
    return palette
