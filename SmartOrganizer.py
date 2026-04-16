import os
import shutil
import hashlib
import datetime
import ctypes
import sys
import threading
import time
import math
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

import customtkinter as ctk
ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

try:
    myappid = 'organizer.smart'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

DEFAULT_CATEGORIES = {
    'Images': ['.jpg', '.jpeg', '.jfif', '.pjpeg', '.pjp', '.svg', '.webp', '.ico', '.cur', '.tiff', '.avif', '.apng', '.png', '.gif', '.bmp'],
    'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.xls', '.xlsx', '.xlsm', '.ppt', '.pptx', '.pptm', '.csv'],
    'Videos': ['.mp4', '.m4v', '.mp4v', '.3gp', '.3gp2', '.avi', '.mkv', '.mov', '.qt', '.wmv', '.flv', '.webm', '.ogv', '.asf', '.ts'],
    'Audio': ['.mp3', '.wav', '.wma', '.aac', '.flac', '.ogg', '.m4a'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.gzip', '.bz2', '.xz'],
    'Disk & Media': ['.iso', '.bin', '.cue', '.mdf', '.mds', '.nrg', '.ccd', '.img', '.sub', '.chd', '.vmdk', '.vhd', '.vhdx', '.vdi'],
    'Executables': ['.apk', '.appx', '.exe', '.msi', '.msp', '.msu', '.bat', '.cmd', '.ps1'],
    'Ebooks': ['.epub', '.mobi', '.azw', '.azw3', '.fb2', '.cbz', '.cbr', '.lit', '.djvu']
}

def format_size(size_bytes):
    if size_bytes == 0: return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192): hasher.update(chunk)
        return hasher.hexdigest()
    except: return None

if DND_AVAILABLE:
    class SmartRoot(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class SmartRoot(ctk.CTk):
        pass

class SmartOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Organizer")
        
        self.root.geometry("1100x750")
        self.root.minsize(900, 650)
        
        self.base_font = ('Courier New', 12)
        self.btn_font = ('Courier New', 12, 'bold')
        self.title_font = ('Courier New', 14, 'bold')
        self.small_font = ('Courier New', 10)
        self.tree_font = ('Courier New', 11)
        self.heading_font = ('Courier New', 12, 'bold')

        self.publisher = "ChewT00TH"
        self.scanned_data = []
        self.item_to_data = {}
        self.size_sort_reverse = False
        self.cat_entries = []
        
        self.load_prefs()
        
        icon_path = "SmartOrganizer.ico"
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "SmartOrganizer.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
        self.bg_color = "#282a36"
        self.fg_color = "#f8f8f2"
        self.accent_bg = "#44475a"
        self.purple = "#bd93f9"
        self.green = "#50fa7b"
        self.cyan = "#8be9fd"
        self.pink = "#ff79c6"
        self.red = "#ff5555"
        self.dracula_comment = "#6272a4"
        
        self.root.configure(bg=self.bg_color)
        self.setup_ui()

    def load_prefs(self):
        try:
            with open("categories.json", "r") as f:
                self.file_categories = json.load(f)
        except:
            self.file_categories = DEFAULT_CATEGORIES.copy()

    def save_prefs(self):
        new_cats = {}
        for entry, exts in self.cat_entries:
            new_name = entry.get().strip()
            if new_name:
                new_cats[new_name] = exts
        self.file_categories = new_cats
        try:
            with open("categories.json", "w") as f:
                json.dump(self.file_categories, f)
            messagebox.showinfo("Saved", "Preferences saved successfully!")
        except:
            messagebox.showerror("Error", "Could not save preferences.")

    def reset_prefs(self):
        if messagebox.askyesno("Confirm", "Reset categories to default?"):
            self.file_categories = DEFAULT_CATEGORIES.copy()
            self.populate_prefs()
            self.save_prefs()

    def hide_progress(self):
        self.progress.set(0)
        self.progress.configure(progress_color="transparent", fg_color=self.accent_bg)
        self.lbl_status.configure(text="...Ready to Scan Files Select Source/Target Folders", text_color=self.cyan)
        self.root.update_idletasks()

    def reset_scan(self):
        self.lbl_source.configure(text="None selected")
        self.lbl_target.configure(text="None selected")
        self.tree.delete(*self.tree.get_children())
        self.scanned_data = []
        self.item_to_data.clear()
        self.size_sort_reverse = False
        self.tree.heading("Size", text="[ Size ↕ ]")
        self.hide_progress()
        self.btn_preview.configure(text="Generate Quick Look", state="normal")
        self.set_action_buttons_disabled()

    def set_action_buttons_disabled(self):
        self.btn_apply.configure(state="disabled", fg_color=self.bg_color, border_width=2, border_color=self.accent_bg, text_color_disabled=self.dracula_comment)
        self.btn_delete.configure(state="disabled", fg_color=self.bg_color, border_width=2, border_color=self.accent_bg, text_color_disabled=self.dracula_comment)

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Treeview", background=self.bg_color, foreground=self.fg_color, fieldbackground=self.bg_color, borderwidth=0, rowheight=28, font=self.tree_font)
        style.configure("Treeview.Heading", background=self.accent_bg, foreground=self.cyan, font=self.heading_font, relief="flat")
        
        style.map("Treeview", background=[('selected', self.purple)], foreground=[('selected', self.bg_color)])
        style.map("Treeview.Heading", background=[('active', self.accent_bg)], foreground=[('active', self.cyan)])

        self.tabview = ctk.CTkTabview(self.root, fg_color=self.bg_color, segmented_button_selected_color=self.purple, segmented_button_selected_hover_color=self.pink, text_color=self.fg_color, height=36)
        self.tabview._segmented_button.configure(font=self.btn_font)
        self.tabview.pack(fill="both", expand=True, padx=12, pady=6)
        
        self.tab_main = self.tabview.add("Organizer")
        self.tab_prefs = self.tabview.add("Preferences")

        ctk.CTkLabel(self.tab_main, text="⚙️ Settings", text_color=self.pink, font=self.title_font).pack(side="top", anchor="w", padx=12, pady=(6, 0))
        config_frame = ctk.CTkFrame(self.tab_main, fg_color=self.bg_color, border_width=2, border_color=self.accent_bg, corner_radius=8)
        config_frame.pack(side="top", fill="x", padx=8, pady=4)

        self.btn_source = ctk.CTkButton(config_frame, text="Source Folder", command=self.pick_source, font=self.btn_font, fg_color=self.accent_bg, hover_color=self.purple, corner_radius=6, width=140, height=30)
        self.btn_source.grid(row=0, column=0, pady=8, padx=8, sticky="ew")
        
        self.lbl_source = ctk.CTkLabel(config_frame, text="None selected", width=200, anchor="w", text_color=self.fg_color, font=self.base_font)
        self.lbl_source.grid(row=0, column=1, sticky="w", padx=8)

        ctk.CTkLabel(config_frame, text="Sort By:", text_color=self.fg_color, font=self.base_font).grid(row=0, column=2, sticky="e", padx=8)
        sort_options = ["None", "Extension", "File Type", "Type and Extension", "Creation Year", "Year and Month"]
        self.sort_var = tk.StringVar(value="File Type")
        sort_opts = ctk.CTkOptionMenu(config_frame, variable=self.sort_var, values=sort_options, font=self.base_font, dropdown_font=self.base_font, fg_color=self.accent_bg, button_color=self.accent_bg, corner_radius=6, width=180, height=30, command=self.refresh_preview)
        sort_opts.grid(row=0, column=3, sticky="w", padx=8)

        self.btn_reset = ctk.CTkButton(config_frame, text="Reset Scan", command=self.reset_scan, font=self.btn_font, fg_color=self.accent_bg, hover_color=self.red, text_color=self.fg_color, corner_radius=6, width=140, height=30)
        self.btn_reset.grid(row=1, column=0, pady=8, padx=8, sticky="ew")

        ctk.CTkLabel(config_frame, text="Skip Exts:", text_color=self.fg_color, font=self.base_font).grid(row=1, column=2, sticky="e", padx=8)
        self.skip_entry = ctk.CTkEntry(config_frame, font=self.base_font, width=180, height=30, fg_color=self.accent_bg, border_width=0, corner_radius=6)
        self.skip_entry.insert(0, ".ini, .sys, .tmp")
        self.skip_entry.grid(row=1, column=3, sticky="w", padx=8)

        self.btn_target = ctk.CTkButton(config_frame, text="Target Folder", command=self.pick_target, font=self.btn_font, fg_color=self.accent_bg, hover_color=self.purple, corner_radius=6, width=140, height=30)
        self.btn_target.grid(row=2, column=0, pady=8, padx=8, sticky="ew")
        
        self.lbl_target = ctk.CTkLabel(config_frame, text="None selected", width=200, anchor="w", text_color=self.fg_color, font=self.base_font)
        self.lbl_target.grid(row=2, column=1, sticky="w", padx=8)

        self.dedup_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(config_frame, text="Deduplicate", font=self.btn_font, variable=self.dedup_var, fg_color=self.purple, text_color=self.fg_color, checkbox_height=18, checkbox_width=18).grid(row=2, column=2, sticky="w", padx=8, pady=4)

        self.fix_ext_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(config_frame, text="Fix Extensions", font=self.btn_font, variable=self.fix_ext_var, fg_color=self.purple, text_color=self.fg_color, checkbox_height=18, checkbox_width=18).grid(row=2, column=3, sticky="w", padx=8, pady=4)

        self.btn_preview = ctk.CTkButton(config_frame, text="Generate Quick Look", command=self.run_preview, fg_color=self.purple, hover_color=self.pink, text_color=self.bg_color, font=self.title_font, corner_radius=8, height=36)
        self.btn_preview.grid(row=3, column=0, columnspan=4, sticky="ew", padx=8, pady=10)

        if DND_AVAILABLE:
            self.btn_source.drop_target_register(DND_FILES)
            self.btn_source.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.lbl_source))
            self.lbl_source.drop_target_register(DND_FILES)
            self.lbl_source.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.lbl_source))
            
            self.btn_target.drop_target_register(DND_FILES)
            self.btn_target.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.lbl_target))
            self.lbl_target.drop_target_register(DND_FILES)
            self.lbl_target.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.lbl_target))

        self.lbl_pub = ctk.CTkLabel(self.tab_main, text=f"Program Made By {self.publisher}", text_color=self.dracula_comment, font=self.small_font)
        self.lbl_pub.pack(side="bottom", pady=(0, 4))

        btn_frame = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
        
        self.progress = ctk.CTkProgressBar(btn_frame, orientation="horizontal", width=250, height=14, fg_color=self.bg_color, progress_color=self.bg_color)
        self.progress.set(0) 
        self.progress.pack(side="left", padx=6)

        self.lbl_status = ctk.CTkLabel(btn_frame, text="...Ready to Scan Files Select Source/Target Folders", text_color=self.cyan, font=self.btn_font)
        self.lbl_status.pack(side="left", padx=6)
        
        self.btn_apply = ctk.CTkButton(btn_frame, text="Apply Changes", command=self.run_apply, fg_color="transparent", hover_color=self.cyan, border_width=1, border_color=self.accent_bg, text_color=self.accent_bg, text_color_disabled=self.accent_bg, font=self.title_font, corner_radius=6, height=36, state="disabled")
        self.btn_apply.pack(side="right", padx=4)

        self.btn_delete = ctk.CTkButton(btn_frame, text="Delete Checked", command=self.delete_selected, fg_color="transparent", hover_color=self.pink, border_width=1, border_color=self.accent_bg, text_color=self.accent_bg, text_color_disabled=self.accent_bg, font=self.title_font, corner_radius=6, height=36, state="disabled")
        self.btn_delete.pack(side="right", padx=4)

        ctk.CTkLabel(self.tab_main, text="🔍 Quick Look", text_color=self.pink, font=self.title_font).pack(side="top", anchor="w", padx=12, pady=(4, 0))
        preview_frame = ctk.CTkFrame(self.tab_main, fg_color=self.bg_color, border_width=2, border_color=self.accent_bg, corner_radius=8)
        preview_frame.pack(side="top", fill="both", expand=True, padx=8, pady=(0, 8))

        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        tree_xscroller = ttk.Scrollbar(preview_frame, orient="horizontal")
        tree_yscroller = ttk.Scrollbar(preview_frame, orient="vertical")

        cols = ("✔", "Action", "File", "Size", "Details")
        self.tree = ttk.Treeview(preview_frame, columns=cols, show="headings", selectmode="extended", 
                                 xscrollcommand=tree_xscroller.set, yscrollcommand=tree_yscroller.set)
        
        self.tree.tag_configure("delete_mark", foreground=self.red, background="#3f262d")

        for col in cols:
            if col == "✔":
                self.tree.heading(col, text="✔", anchor="center")
                self.tree.column(col, width=40, minwidth=40, stretch=False, anchor="center")
            elif col == "Action":
                self.tree.heading(col, text=col, anchor="w")
                self.tree.column(col, width=80, minwidth=80, stretch=False, anchor="w")
            elif col == "File":
                self.tree.heading(col, text=col, anchor="w")
                self.tree.column(col, width=280, minwidth=150, stretch=False, anchor="w")
            elif col == "Size":
                self.tree.heading(col, text="[ Size ↕ ]", command=self.sort_by_size, anchor="center")
                self.tree.column(col, width=140, minwidth=140, stretch=False, anchor="center")
            elif col == "Details":
                self.tree.heading(col, text=col, anchor="w")
                self.tree.column(col, width=450, minwidth=250, stretch=True, anchor="w") 

        tree_xscroller.config(command=self.tree.xview)
        tree_yscroller.config(command=self.tree.yview)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        tree_yscroller.grid(row=0, column=1, sticky="ns", pady=4)
        tree_xscroller.grid(row=1, column=0, sticky="ew", padx=4)

        tip_text = "💡 Tip: Drag & Drop folders onto the buttons! | Select rows with Shift/Click, press Space to check for Deletion." if DND_AVAILABLE else "💡 Tip: Select rows with Shift/Ctrl+Click. Press Spacebar to check."
        self.lbl_tip = ctk.CTkLabel(preview_frame, text=tip_text, text_color=self.cyan, font=self.small_font)
        self.lbl_tip.grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=4)

        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.tree.bind("<Motion>", self.on_tree_motion)
        self.tree.bind("<space>", self.toggle_selected_checkboxes)

        self.set_action_buttons_disabled()
        self.setup_prefs_ui(self.btn_font, self.base_font)

    def on_drop(self, event, label_widget):
        path = event.data.strip()
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        
        if os.path.isdir(path):
            label_widget.configure(text=path)
        else:
            messagebox.showwarning("Invalid", "Please drag and drop a valid folder, not a file.")

    def setup_prefs_ui(self, btn_font, base_font):
        ctk.CTkLabel(self.tab_prefs, text="Customize Folder Names", font=self.title_font, text_color=self.cyan).pack(pady=10)
        
        self.prefs_scroll = ctk.CTkScrollableFrame(self.tab_prefs, fg_color=self.accent_bg, corner_radius=8)
        self.prefs_scroll.pack(fill="both", expand=True, padx=16, pady=8)
        
        self.populate_prefs(btn_font, base_font)
        
        prefs_btn_frame = ctk.CTkFrame(self.tab_prefs, fg_color="transparent")
        prefs_btn_frame.pack(fill="x", padx=16, pady=8)
        
        ctk.CTkButton(prefs_btn_frame, text="Save Preferences", command=self.save_prefs, fg_color=self.green, hover_color=self.cyan, text_color=self.bg_color, font=btn_font, height=38).pack(side="right", padx=6)
        ctk.CTkButton(prefs_btn_frame, text="Reset Defaults", command=self.reset_prefs, fg_color=self.red, hover_color=self.pink, text_color=self.bg_color, font=btn_font, height=38).pack(side="right", padx=6)

    def populate_prefs(self, btn_font=None, base_font=None):
        if not btn_font: btn_font = ('Courier New', 12, 'bold')
        if not base_font: base_font = ('Courier New', 12)

        for widget in self.prefs_scroll.winfo_children():
            widget.destroy()
        self.cat_entries = []
        for cat, exts in self.file_categories.items():
            row_frame = ctk.CTkFrame(self.prefs_scroll, fg_color=self.accent_bg, corner_radius=6)
            row_frame.pack(fill="x", pady=6, padx=8)
            
            entry = ctk.CTkEntry(row_frame, width=200, height=36, font=btn_font, fg_color=self.bg_color, text_color=self.fg_color, border_width=0)
            entry.insert(0, cat)
            entry.pack(side="left", padx=14, pady=8)
            
            ext_str = ", ".join(exts)
            if len(ext_str) > 60: ext_str = ext_str[:57] + "..."
            ctk.CTkLabel(row_frame, text=ext_str, text_color=self.fg_color, font=base_font).pack(side="left", padx=8)
            
            self.cat_entries.append((entry, exts))

    def on_tree_motion(self, event):
        region = self.tree.identify_region(event.x, event.y)
        col = self.tree.identify_column(event.x)
        style = ttk.Style()
        
        if region == "cell" and col == "#1":
            self.tree.configure(cursor="hand2")
            style.map("Treeview.Heading", background=[('active', self.accent_bg)], foreground=[('active', self.cyan)])
        elif region == "heading" and col == "#4":
            self.tree.configure(cursor="hand2")
            style.map("Treeview.Heading", background=[('active', self.purple)], foreground=[('active', self.bg_color)])
        else:
            self.tree.configure(cursor="")
            style.map("Treeview.Heading", background=[('active', self.accent_bg)], foreground=[('active', self.cyan)])

    def on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            col = self.tree.identify_column(event.x)
            if col == "#1":
                row_id = self.tree.identify_row(event.y)
                if row_id:
                    vals = list(self.tree.item(row_id, "values"))
                    new_state = "☐" if vals[0] == "☑" else "☑"
                    
                    selected_items = self.tree.selection()
                    if row_id in selected_items and len(selected_items) > 1:
                        for item in selected_items:
                            item_vals = list(self.tree.item(item, "values"))
                            item_vals[0] = new_state
                            tags = ("delete_mark",) if new_state == "☑" else ()
                            self.tree.item(item, values=item_vals, tags=tags)
                    else:
                        vals[0] = new_state
                        tags = ("delete_mark",) if new_state == "☑" else ()
                        self.tree.item(row_id, values=vals, tags=tags)
                        
                    self.update_button_states()

    def toggle_selected_checkboxes(self, event):
        selected_items = self.tree.selection()
        if not selected_items: return
        
        first_vals = list(self.tree.item(selected_items[0], "values"))
        new_state = "☐" if first_vals[0] == "☑" else "☑"
        
        for item in selected_items:
            vals = list(self.tree.item(item, "values"))
            vals[0] = new_state
            tags = ("delete_mark",) if new_state == "☑" else ()
            self.tree.item(item, values=vals, tags=tags)
            
        self.update_button_states()

    def update_button_states(self):
        has_checked = any(self.tree.item(iid, "values")[0] == "☑" for iid in self.tree.get_children())
        if has_checked:
            self.btn_delete.configure(state="normal", fg_color=self.red, border_width=0, text_color=self.bg_color)
        else:
            self.btn_delete.configure(state="disabled", fg_color=self.bg_color, border_width=2, border_color=self.accent_bg, text_color_disabled=self.dracula_comment)
            
        if self.tree.get_children():
            self.btn_apply.configure(state="normal", fg_color=self.green, border_width=0, text_color=self.bg_color)
        else:
            self.btn_apply.configure(state="disabled", fg_color=self.bg_color, border_width=2, border_color=self.accent_bg, text_color_disabled=self.dracula_comment)

    def sort_by_size(self):
        if not self.scanned_data: return
        self.size_sort_reverse = not self.size_sort_reverse
        self.scanned_data.sort(key=lambda x: x['raw_size'], reverse=self.size_sort_reverse)
        arrow = "▼" if self.size_sort_reverse else "▲"
        self.tree.heading("Size", text=f"[ Size {arrow} ]")
        self.refresh_preview()

    def delete_selected(self):
        checked_items = [iid for iid in self.tree.get_children() if self.tree.item(iid, "values")[0] == "☑"]
        if not checked_items: return
            
        if not messagebox.askyesno("Warning", f"Permanently delete {len(checked_items)} checked file(s)?\n\nThis will remove them from your computer immediately. This cannot be undone!"):
            return
            
        success_count = 0
        for iid in checked_items:
            data = self.item_to_data.get(iid)
            if data:
                try:
                    os.remove(data['src'])
                    if data in self.scanned_data:
                        self.scanned_data.remove(data)
                    success_count += 1
                except:
                    pass
                    
        messagebox.showinfo("Deleted", f"Successfully deleted {success_count} file(s).")
        self.refresh_preview()

    def pick_source(self):
        folder = filedialog.askdirectory()
        if folder: self.lbl_source.configure(text=folder)

    def pick_target(self):
        folder = filedialog.askdirectory()
        if folder: self.lbl_target.configure(text=folder)

    def _update_progress_ui(self, current_val, total_val, action_text="Processing"):
        if total_val > 0: self.progress.set(current_val / total_val) 
        self.lbl_status.configure(text=f"{action_text}: {current_val}/{total_val}")

    def run_preview(self):
        src = self.lbl_source.cget("text")
        dst = self.lbl_target.cget("text")
        if src == "None selected" or dst == "None selected":
            messagebox.showwarning("Error", "Select folders first.")
            return
        
        self.progress.configure(progress_color=self.purple)
        self.progress.set(0)
        self.root.update_idletasks() 
        
        self.btn_preview.configure(text="Scanning...", state="disabled")
        self.set_action_buttons_disabled()
        self.tree.heading("Size", text="[ Size ↕ ]")
        self.size_sort_reverse = False
        for item in self.tree.get_children(): self.tree.delete(item)
        self.scanned_data = []
        threading.Thread(target=self._preview_worker, args=(src, dst), daemon=True).start()

    def _preview_worker(self, src, dst):
        signatures = {b'\xFF\xD8\xFF': '.jpg', b'\x89PNG\r\n\x1a\n': '.png', b'%PDF-': '.pdf', b'PK\x03\x04': '.zip'}
        total_files = sum([len(files) for r, d, files in os.walk(src)])
        if total_files == 0:
            self.root.after(0, self._finish_scan)
            return
            
        seen_sizes = {}
        skip_exts = [e.strip().lower() for e in self.skip_entry.get().split(",") if e.strip()]
        processed = 0
        
        for root, _, files in os.walk(src):
            for file in files:
                processed += 1
                if processed % 5 == 0: self.root.after(0, self._update_progress_ui, processed, total_files, "Scanning")
                
                filepath = os.path.join(root, file)
                name, ext = os.path.splitext(file)
                ext = ext.lower()
                if ext in skip_exts: continue
                
                raw_size = os.path.getsize(filepath)
                readable_size = format_size(raw_size)
                final_ext = ext
                
                if self.fix_ext_var.get():
                    try:
                        with open(filepath, 'rb') as f:
                            header = f.read(8)
                            for magic, mext in signatures.items():
                                if header.startswith(magic):
                                    if not (mext == '.zip' and ext not in ["", ".tmp", ".bak"]):
                                        final_ext = mext; break
                    except: pass
                
                is_duplicate = False
                dup_details = ""
                if self.dedup_var.get():
                    if raw_size in seen_sizes:
                        h = get_file_hash(filepath)
                        for s in seen_sizes[raw_size]:
                            if s['hash'] is None: s['hash'] = get_file_hash(s['path'])
                            if h == s['hash']:
                                is_duplicate = True
                                dup_details = f"Duplicate of {s['name']}"
                                break
                        if not is_duplicate:
                            seen_sizes[raw_size].append({'path': filepath, 'hash': h, 'name': name+final_ext})
                    else: seen_sizes[raw_size] = [{'path': filepath, 'hash': None, 'name': name+final_ext}]
                
                self.scanned_data.append({
                    'file': file,
                    'name': name,
                    'ext': final_ext,
                    'src': filepath,
                    'raw_size': raw_size,
                    'readable_size': readable_size,
                    'is_duplicate': is_duplicate,
                    'dup_details': dup_details,
                    'c_time': os.path.getctime(filepath)
                })

        self.root.after(0, self._finish_scan)

    def _finish_scan(self):
        self.progress.configure(progress_color=self.green)
        self.progress.set(1.0)
        self.lbl_status.configure(text="Scan Complete! Analyzing...", text_color=self.green)
        self.root.update_idletasks() 
        
        self.btn_preview.configure(text="Generate Quick Look", state="normal")
        self.root.after(100, self.refresh_preview)

    def refresh_preview(self, choice=None):
        if not self.scanned_data: return
        dst = self.lbl_target.cget("text")
        if dst == "None selected": return
        
        for item in self.tree.get_children(): self.tree.delete(item)
        self.item_to_data.clear()
        
        sort_mode = self.sort_var.get()
        
        for data in self.scanned_data:
            if data['is_duplicate']:
                iid = self.tree.insert("", "end", values=("☑", "DELETE", data['file'], data['readable_size'], data['dup_details']), tags=("delete_mark",))
                self.item_to_data[iid] = data
                continue
                
            sub = ""
            d_obj = datetime.datetime.fromtimestamp(data['c_time'])
            if sort_mode == "Extension": sub = data['ext'].strip('.').upper()
            elif sort_mode == "File Type":
                sub = 'Other'
                for ftype, exts in self.file_categories.items():
                    if data['ext'] in exts: sub = ftype; break
            elif sort_mode == "Type and Extension":
                ft = 'Other'
                for ftype, exts in self.file_categories.items():
                    if data['ext'] in exts: ft = ftype; break
                sub = os.path.join(ft, data['ext'].strip('.').upper())
            elif sort_mode == "Creation Year": sub = d_obj.strftime("%Y")
            elif sort_mode == "Year and Month": sub = d_obj.strftime("%Y-%m")
            
            t_dir = os.path.join(dst, sub)
            t_path = os.path.join(t_dir, data['name'] + data['ext'])
            c = 1
            while os.path.exists(t_path) and t_path != data['src']:
                t_path = os.path.join(t_dir, f"{data['name']}_{c}{data['ext']}"); c += 1
                
            iid = self.tree.insert("", "end", values=("☐", "MOVE", data['file'], data['readable_size'], t_path))
            self.item_to_data[iid] = data

        max_file_width = 280
        max_details_width = 450
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            f_width = len(str(vals[2])) * 8 + 20
            d_width = len(str(vals[4])) * 8 + 20
            if f_width > max_file_width: max_file_width = f_width
            if d_width > max_details_width: max_details_width = d_width
            
        if max_file_width > 500: max_file_width = 500
        if max_details_width > 900: max_details_width = 900
            
        self.tree.column("File", width=int(max_file_width))
        self.tree.column("Details", width=int(max_details_width))

        self.update_button_states()

    def run_apply(self):
        planned_operations = []
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            data = self.item_to_data[iid]
            if vals[0] == "☑":
                planned_operations.append({"action": "delete", "src": data['src']})
            elif vals[1] == "MOVE":
                dst_path = vals[4]
                planned_operations.append({"action": "move", "src": data['src'], "dst": dst_path, "dst_dir": os.path.dirname(dst_path)})

        if not planned_operations: return
        if not messagebox.askyesno("Confirm", "Apply changes?"): return
        
        self.progress.configure(fg_color=self.accent_bg, progress_color=self.pink)
        self.progress.set(0)
        self.root.update_idletasks()
        
        self.set_action_buttons_disabled()
        threading.Thread(target=self._apply_worker, args=(planned_operations,), daemon=True).start()

    def _apply_worker(self, planned_operations):
        total = len(planned_operations)
        success = 0
        for i, op in enumerate(planned_operations):
            self.root.after(0, self._update_progress_ui, i + 1, total, "Moving")
            try:
                if op["action"] == "delete": os.remove(op["src"])
                else:
                    if not os.path.exists(op["dst_dir"]): os.makedirs(op["dst_dir"])
                    shutil.move(op["src"], op["dst"])
                success += 1
            except: pass
        self.root.after(0, self._finish_apply, success)

    def _finish_apply(self, success):
        self.progress.configure(fg_color=self.green, progress_color=self.green)
        self.progress.set(1.0)
        self.lbl_status.configure(text="Processing Done!", text_color=self.green)
        self.root.update_idletasks()
        
        messagebox.showinfo("Done", f"Processed {success} files.")
        for item in self.tree.get_children(): self.tree.delete(item)
        self.scanned_data = []
        self.item_to_data.clear()
        
        self.set_action_buttons_disabled()
        self.root.after(2000, self.hide_progress)

if __name__ == "__main__":
    root = SmartRoot()
    app = SmartOrganizerApp(root)
    root.mainloop()
