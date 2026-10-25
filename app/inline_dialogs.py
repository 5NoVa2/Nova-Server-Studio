"""Messages and confirmations rendered inside the existing app window."""
from bubble_ui import BubbleButton, BubbleNotebook, BubbleCard, Launcher
import tkinter as tk
from tkinter import ttk,messagebox


def install(root):
    def dialog(title,message,choices):
        value=tk.StringVar(root,value='')
        cover=ttk.Frame(root,style='Card.TFrame',padding=30)
        cover.place(relx=.5,rely=.5,anchor='center',relwidth=.88)
        cover.lift()
        ttk.Label(cover,text=title,style='Section.TLabel').pack(anchor='w')
        ttk.Label(cover,text=str(message),style='Card.TLabel',wraplength=730).pack(anchor='w',pady=18)
        row=ttk.Frame(cover,style='Card.TFrame');row.pack(fill='x')
        previous=root.grab_current()
        for label,result in choices:
            BubbleButton(row,text=label,command=lambda r=result:value.set(r)).pack(side='right',padx=6)
        cover.grab_set();root.wait_variable(value)
        cover.grab_release();cover.destroy()
        if previous and previous.winfo_exists():previous.grab_set()
        return value.get()
    def ask(title='',message='',**kwargs):return dialog(title,message,[('Continue','yes'),('Cancel','no')])=='yes'
    def tell(title='',message='',**kwargs):dialog(title,message,[('OK','ok')]);return 'ok'
    messagebox.askyesno=ask;messagebox.askokcancel=ask
    messagebox.showerror=tell;messagebox.showwarning=tell;messagebox.showinfo=tell
