"""Nova dark theme, implemented with standard-library Tk/ttk."""
from tkinter import ttk,font as tkfont

BG='#08090c'
CARD='#111318'
TEXT='#e6edf7'
MUTED='#9cabc2'
ACCENT='#d9deea'


def apply_theme(root):
    families={family.casefold():family for family in tkfont.families(root)}
    FONT=families.get('segoe ui',families.get('dejavu sans',families.get('helvetica','Arial')))
    DISPLAY_FONT=families.get('segoe ui light',FONT)
    import bubble_ui
    bubble_ui.FONT=FONT; bubble_ui.DISPLAY_FONT=DISPLAY_FONT
    root.configure(background=BG)
    style=ttk.Style(root)
    style.theme_use('clam')
    style.configure('.',font=(FONT,10),background=BG,foreground=TEXT)
    style.configure('TFrame',background=BG)
    style.configure('Card.TFrame',background=CARD)
    style.configure('TLabel',background=BG,foreground=TEXT)
    style.configure('Muted.TLabel',foreground=MUTED)
    style.configure('Brand.TLabel',foreground=ACCENT,font=(FONT,11,'bold'))
    style.configure('Title.TLabel',font=(DISPLAY_FONT,22))
    style.configure('Card.TLabel',background=CARD)
    style.configure('CardMuted.TLabel',background=CARD,foreground=MUTED)
    style.configure('Section.TLabel',background=CARD,font=(FONT,14,'bold'))
    style.configure('Status.TLabel',background='#172b2c',foreground=ACCENT,padding=(12,8))
    style.configure('TButton',background='#222631',foreground=TEXT,borderwidth=0,padding=(13,10),focusthickness=0)
    style.map('TButton',background=[('disabled','#182233'),('pressed','#31445e'),('active','#2c3e57')],foreground=[('disabled','#61718a')])
    style.configure('Primary.TButton',background=ACCENT,foreground='#08251e',font=(FONT,10,'bold'))
    style.map('Primary.TButton',background=[('disabled','#223f3d'),('pressed','#3dbb9e'),('active','#8cf1d7')],foreground=[('disabled','#6b8982')])
    style.configure('Danger.TButton',background='#392735',foreground='#ffb4b4')
    style.map('Danger.TButton',background=[('active','#513042')])
    style.configure('TEntry',fieldbackground='#0d0f15',foreground=TEXT,insertcolor=TEXT,bordercolor='#303541',padding=8)
    style.map('TEntry',bordercolor=[('focus',ACCENT)],lightcolor=[('focus',ACCENT)],darkcolor=[('focus',ACCENT)])
    style.configure('TSpinbox',fieldbackground='#0d0f15',foreground=TEXT,insertcolor=TEXT,arrowcolor=MUTED,bordercolor='#303541',padding=8)
    style.configure('TCheckbutton',background=CARD,foreground=TEXT,padding=(0,4))
    style.map('TCheckbutton',background=[('active',CARD)],indicatorbackground=[('selected',ACCENT),('!selected','#26364e')])
    style.configure('TSeparator',background='#28364b')
    style.configure('Vertical.TScrollbar',background='#303541',troughcolor='#0a101a',borderwidth=0,arrowcolor=MUTED)
    style.configure('TCombobox',fieldbackground='#0d0f15',background='#222631',foreground=TEXT,arrowcolor=ACCENT,padding=6)
    style.map('TCombobox',fieldbackground=[('readonly','#0d0f15'),('disabled','#17202d')],foreground=[('readonly',TEXT),('disabled',MUTED)],selectbackground=[('readonly','#0d0f15')],selectforeground=[('readonly',TEXT)])
    root.option_add('*TCombobox*Listbox.background','#15181f')
    root.option_add('*TCombobox*Listbox.foreground',TEXT)
    root.option_add('*TCombobox*Listbox.selectBackground','#353b48')
    style.configure('Treeview',background='#0d0f15',fieldbackground='#0d0f15',foreground=TEXT,rowheight=30,borderwidth=0)
    style.configure('Treeview.Heading',background='#222631',foreground=TEXT,padding=8)
    style.map('Treeview',background=[('selected','#353b48')],foreground=[('selected','#ffffff')])
    style.configure('TNotebook',background=BG,borderwidth=0)
    style.configure('TNotebook.Tab',background='#1a1d25',foreground=MUTED,padding=(16,11))
    style.map('TNotebook.Tab',background=[('selected','#353b48'),('active','#2c3e57')],foreground=[('selected','#ecfff9')])
    style.configure('Logo.TLabel',font=(DISPLAY_FONT,22),foreground=ACCENT)
    style.configure('Join.TLabel',background='#101e2c',foreground='#c5e8df',font=(FONT,10,'bold'))
    style.configure('IdleBadge.TLabel',background='#1c2838',foreground='#9faec3',padding=(12,8),font=(FONT,9,'bold'))
    style.configure('OnlineBadge.TLabel',background='#123d34',foreground='#77f0c8',padding=(12,8),font=(FONT,9,'bold'))
    style.configure('BusyBadge.TLabel',background='#3a3020',foreground='#f0cb83',padding=(12,8),font=(FONT,9,'bold'))
    style.configure('Horizontal.TProgressbar',background=ACCENT,troughcolor='#182638',borderwidth=0)
    style.configure('Catalog.Treeview',rowheight=76,background='#0d0f15',fieldbackground='#0d0f15',foreground=TEXT)
    style.configure('ModCatalog.Treeview',rowheight=52,background='#0d0f15',fieldbackground='#0d0f15',foreground=TEXT)
    style.configure('TEntry',lightcolor='#303540',darkcolor='#303540',bordercolor='#303540',relief='flat',borderwidth=1)
    style.configure('TCombobox',lightcolor='#303540',darkcolor='#303540',bordercolor='#303540',relief='flat',borderwidth=1)
    style.configure('TSpinbox',lightcolor='#303540',darkcolor='#303540',bordercolor='#303540',relief='flat',borderwidth=1)
    style.configure('Treeview',lightcolor='#272c36',darkcolor='#272c36',bordercolor='#272c36',relief='flat',borderwidth=0)
    style.configure('Treeview.Heading',lightcolor='#272c36',darkcolor='#272c36',bordercolor='#272c36',relief='flat',borderwidth=0)
    style.configure('Vertical.TScrollbar',lightcolor='#252a34',darkcolor='#252a34',bordercolor='#252a34',relief='flat')
    style.configure('Join.TLabel',background='#12161f',foreground='#c8cdd8')
    for name in ('TEntry','TCombobox','TSpinbox','Treeview'):
        style.configure(name,font=(FONT,10))
    style.configure('Treeview.Heading',font=(FONT,9,'bold'))
    root.option_add('*TCombobox*Listbox.font',(FONT,10))
    return style
