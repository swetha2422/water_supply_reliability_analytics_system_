"""
Water Supply Reliability Analytics System
Single-file desktop application: Python Tkinter + MySQL + Matplotlib.

Login:
    Username: xavi
    Password: 123

Before running:
1. Install packages in PyCharm Terminal:
       pip install mysql-connector-python matplotlib
2. Set MYSQL_CONFIG["password"] below to your MySQL root password.
3. Keep water_banner.png in the same folder as this Python file (optional).
4. Database tables must already exist in water_reliability_db.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, datetime

import mysql.connector
from mysql.connector import Error

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ---------------------------- CONFIGURATION ----------------------------

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Uksri3115@",
    "database": "my_app"
}

APP_USERNAME = "xavi"
APP_PASSWORD = "123"

NAVY = "#082746"
NAVY_DARK = "#04182D"
BLUE = "#0879D9"
CYAN = "#13B8D5"
BG = "#F1F6FB"
WHITE = "#FFFFFF"
TEXT = "#17324D"
MUTED = "#6C8197"
GREEN = "#15966A"
ORANGE = "#E99A25"
RED = "#DF4C5A"
BORDER = "#D8E4EF"

# Only these known tables/columns are used in SQL, preventing user-entered
# table names from becoming SQL identifiers.
TABLE_CONFIG = {
    "Areas": {
        "table": "areas",
        "pk": "area_id",
        "columns": [
            ("area_id", "ID", "readonly"),
            ("area_name", "Area Name", "text"),
            ("zone_name", "Zone Name", "text"),
            ("population", "Population", "number"),
        ],
        "search": ["area_name", "zone_name"],
    },
    "Water Supply": {
        "table": "water_supply",
        "pk": "supply_id",
        "columns": [
            ("supply_id", "ID", "readonly"),
            ("area_id", "Area ID", "number"),
            ("supply_date", "Supply Date (YYYY-MM-DD)", "date"),
            ("scheduled_minutes", "Scheduled Minutes", "number"),
            ("actual_minutes", "Actual Minutes", "number"),
            ("interruption_minutes", "Interruption Minutes", "number"),
            ("supply_status", "Status (Normal/Delayed/Interrupted)", "status"),
        ],
        "search": ["supply_status", "supply_date"],
    },
    "Water Issues": {
        "table": "water_issues",
        "pk": "issue_id",
        "columns": [
            ("issue_id", "ID", "readonly"),
            ("supply_id", "Supply ID", "number"),
            ("issue_type", "Issue Type", "text"),
            ("severity", "Severity (Low/Medium/High)", "severity"),
            ("issue_description", "Description", "text"),
        ],
        "search": ["issue_type", "severity", "issue_description"],
    },
    "Maintenance": {
        "table": "maintenance_records",
        "pk": "maintenance_id",
        "columns": [
            ("maintenance_id", "ID", "readonly"),
            ("issue_id", "Issue ID", "number"),
            ("maintenance_date", "Maintenance Date (YYYY-MM-DD)", "date_optional"),
            ("repair_minutes", "Repair Minutes", "number"),
            ("maintenance_status", "Status (Pending/In Progress/Completed)", "maintenance_status"),
        ],
        "search": ["maintenance_status"],
    },
}


def db_connect():
    return mysql.connector.connect(**MYSQL_CONFIG)


def query_rows(sql, params=()):
    conn = db_connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


def execute_sql(sql, params=()):
    conn = db_connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


def safe_int(value, label, allow_blank=False):
    value = str(value).strip()
    if allow_blank and value == "":
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"{label} must be a whole number.")


def validate_date(value, label, allow_blank=False):
    value = str(value).strip()
    if allow_blank and value == "":
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        raise ValueError(f"{label} must use YYYY-MM-DD format, for example 2026-03-10.")


# ---------------------------- LOGIN WINDOW ----------------------------

class WaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Water Supply reliability Analytics system")
        self.root.geometry("1380x850")
        self.root.minsize(1100, 700)
        self.root.configure(bg=BG)
        self.current_page = "Dashboard"
        self.search_var = tk.StringVar()
        self.filter_zone_var = tk.StringVar(value="All Zones")
        self.filter_status_var = tk.StringVar(value="All Statuses")
        self.date_from_var = tk.StringVar()
        self.date_to_var = tk.StringVar()
        self.banner_image = None
        self.login_image = None
        self.show_login()

    def show_login(self):
        for child in self.root.winfo_children():
            child.destroy()

        self.root.configure(bg=NAVY_DARK)
        wrapper = tk.Frame(self.root, bg=NAVY_DARK)
        wrapper.pack(fill="both", expand=True)

        # A water image is shown when water_banner.png is beside this .py file.
        try:
            from pathlib import Path
            image_path = Path(__file__).with_name("water_banner.png")
            if image_path.exists():
                self.login_image = tk.PhotoImage(file=str(image_path))
                image_label = tk.Label(wrapper, image=self.login_image, bd=0, bg=NAVY_DARK)
                image_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        except Exception:
            self.login_image = None

        overlay = tk.Frame(wrapper, bg=NAVY, highlightbackground="#2B82B8", highlightthickness=1)
        overlay.place(relx=0.5, rely=0.5, anchor="center", width=430, height=535)

        tk.Label(overlay, text="💧", font=("Segoe UI Emoji", 40), bg=NAVY, fg=CYAN).pack(pady=(28, 2))
        tk.Label(overlay, text="WATER SUPPLY", font=("Segoe UI", 21, "bold"),
                 bg=NAVY, fg=WHITE).pack()
        tk.Label(overlay, text="RELIABILITY ANALYTICS SYSTEM", font=("Segoe UI", 11, "bold"),
                 bg=NAVY, fg="#9DDCF7").pack(pady=(3, 5))
        tk.Label(overlay, text="Clean Water  •  Healthy Communities  •  Better Tomorrow",
                 font=("Segoe UI", 9), bg=NAVY, fg="#C3D8E8").pack(pady=(0, 23))

        tk.Label(overlay, text="Username", anchor="w", font=("Segoe UI", 10, "bold"),
                 bg=NAVY, fg=WHITE).pack(fill="x", padx=48)
        self.username_entry = ttk.Entry(overlay, font=("Segoe UI", 12))
        self.username_entry.pack(fill="x", padx=48, ipady=8, pady=(6, 16))
        self.username_entry.insert(0, "xavi")

        tk.Label(overlay, text="Password", anchor="w", font=("Segoe UI", 10, "bold"),
                 bg=NAVY, fg=WHITE).pack(fill="x", padx=48)
        self.password_entry = ttk.Entry(overlay, show="•", font=("Segoe UI", 12))
        self.password_entry.pack(fill="x", padx=48, ipady=8, pady=(6, 22))
        self.password_entry.insert(0, "")

        login_btn = tk.Button(overlay, text="SIGN IN  →", command=self.login,
                              bg=BLUE, fg=WHITE, activebackground=CYAN, activeforeground=WHITE,
                              font=("Segoe UI", 11, "bold"), bd=0, cursor="hand2")
        login_btn.pack(fill="x", padx=48, ipady=10)
        self.password_entry.bind("<Return>", lambda _event: self.login())
        self.username_entry.bind("<Return>", lambda _event: self.password_entry.focus_set())

        tk.Label(overlay, text="Default login: xavi  /  123",
                 font=("Segoe UI", 9), bg=NAVY, fg="#9DDCF7").pack(pady=(20, 4))
        tk.Label(overlay, text="Authorized administrator access",
                 font=("Segoe UI", 9), bg=NAVY, fg="#B7C9D8").pack()

        self.root.configure(bg=NAVY_DARK)
        self.username_entry.focus_set()

    def login(self):
        if self.username_entry.get().strip() == APP_USERNAME and self.password_entry.get() == APP_PASSWORD:
            try:
                conn = db_connect()
                conn.close()
            except Error as exc:
                messagebox.showerror(
                    "MySQL Connection Error",
                    "Login details are correct, but MySQL connection failed.\n\n"
                    "Check MYSQL_CONFIG password/database at the top of the code.\n\n" + str(exc)
                )
                return
            self.build_main_app()
        else:
            messagebox.showerror("Login Failed", "Incorrect username or password.\nTry xavi / 123.")

    # ---------------------------- MAIN SHELL ----------------------------

    def build_main_app(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.root.configure(bg=BG)

        header = tk.Frame(self.root, bg=NAVY_DARK, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="💧  WATER SUPPLY RELIABILITY ANALYTICS",
                 bg=NAVY_DARK, fg=WHITE, font=("Segoe UI", 15, "bold")).pack(side="left", padx=24)
        tk.Label(header, text="Admin: xavi", bg=NAVY_DARK, fg="#C4E8FA",
                 font=("Segoe UI", 10, "bold")).pack(side="right", padx=(10, 20))
        tk.Button(header, text="Logout", command=self.logout, bg="#17466D", fg=WHITE,
                  activebackground=RED, activeforeground=WHITE, bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", padx=14, pady=7).pack(side="right", padx=10)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(body, bg=NAVY, width=225)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="WORKSPACE", bg=NAVY, fg="#79B9DE",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(24, 12))

        nav_items = [
            ("▦", "Dashboard"),
            ("⌖", "Areas"),
            ("◉", "Water Supply"),
            ("⚠", "Water Issues"),
            ("🔧", "Maintenance"),
            ("▥", "Analytics"),
        ]
        for symbol, page in nav_items:
            tk.Button(self.sidebar, text=f"  {symbol}    {page}", anchor="w",
                      command=lambda p=page: self.show_page(p),
                      bg="#0D3A61" if page == self.current_page else NAVY,
                      fg=WHITE if page == self.current_page else "#D4E5F2",
                      activebackground=BLUE, activeforeground=WHITE, bd=0,
                      font=("Segoe UI", 10, "bold" if page == self.current_page else "normal"),
                      cursor="hand2", padx=12, pady=13).pack(fill="x", padx=10, pady=3)

        tk.Label(self.sidebar, text="WATER • DATA • DECISIONS", bg=NAVY, fg="#75A7C7",
                 font=("Segoe UI", 8, "bold")).pack(side="bottom", pady=18)

        self.content_canvas = tk.Canvas(body, bg=BG, highlightthickness=0)
        self.content_scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.content_canvas.yview)
        self.content = tk.Frame(self.content_canvas, bg=BG)
        self.content_window = self.content_canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content_canvas.configure(yscrollcommand=self.content_scrollbar.set)
        self.content_canvas.pack(side="left", fill="both", expand=True)
        self.content_scrollbar.pack(side="right", fill="y")
        self.content.bind("<Configure>", lambda _e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")))
        self.content_canvas.bind("<Configure>", lambda e: self.content_canvas.itemconfigure(self.content_window, width=e.width))
        self.content_canvas.bind_all("<MouseWheel>", lambda e: self.content_canvas.yview_scroll(int(-e.delta / 120), "units"))
        self.show_page("Dashboard")

    def logout(self):
        if messagebox.askyesno("Logout", "Do you want to log out?"):
            self.show_login()

    def clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    def show_page(self, page):
        self.current_page = page
        # Rebuild sidebar to reflect selected page
        if hasattr(self, "sidebar") and self.sidebar.winfo_exists():
            for widget in self.sidebar.winfo_children():
                if isinstance(widget, tk.Button):
                    label = widget.cget("text")
                    is_active = label.strip().endswith(page)
                    widget.configure(bg="#0D3A61" if is_active else NAVY,
                                     fg=WHITE if is_active else "#D4E5F2")
        self.clear_content()
        if page == "Dashboard":
            self.render_dashboard()
        elif page == "Analytics":
            self.render_analytics()
        else:
            self.render_crud(page)

    # ---------------------------- COMMON UI ----------------------------

    def page_heading(self, title, subtitle):
        top = tk.Frame(self.content, bg=BG)
        top.pack(fill="x", padx=26, pady=(22, 12))
        tk.Label(top, text=title, bg=BG, fg=TEXT, font=("Segoe UI", 21, "bold")).pack(anchor="w")
        tk.Label(top, text=subtitle, bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))
        return top

    def card(self, parent, title, value, color):
        frame = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        tk.Frame(frame, bg=color, width=5).pack(side="left", fill="y")
        inside = tk.Frame(frame, bg=WHITE)
        inside.pack(side="left", fill="both", expand=True, padx=15, pady=13)
        tk.Label(inside, text=title.upper(), bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        val = tk.Label(inside, text=str(value), bg=WHITE, fg=TEXT,
                       font=("Segoe UI", 23, "bold"))
        val.pack(anchor="w", pady=(3, 0))
        return frame, val

    def get_counts(self):
        return {
            "Areas": query_rows("SELECT COUNT(*) AS n FROM areas")[0]["n"],
            "Water Supply": query_rows("SELECT COUNT(*) AS n FROM water_supply")[0]["n"],
            "Water Issues": query_rows("SELECT COUNT(*) AS n FROM water_issues")[0]["n"],
            "Maintenance": query_rows("SELECT COUNT(*) AS n FROM maintenance_records")[0]["n"],
        }

    def refresh_current(self):
        self.show_page(self.current_page)

    # ---------------------------- DASHBOARD ----------------------------

    def render_dashboard(self):
        self.page_heading("Dashboard", "Live overview of water supply reliability and maintenance.")
        try:
            counts = self.get_counts()
            pending = query_rows(
                "SELECT COUNT(*) AS n FROM water_supply WHERE supply_status = %s", ("Interrupted",)
            )[0]["n"]
            avg_delay = query_rows(
                "SELECT AVG(GREATEST(scheduled_minutes - actual_minutes, 0)) AS n FROM water_supply"
            )[0]["n"] or 0
            avg_delay = round(float(avg_delay), 1)
        except Error as exc:
            messagebox.showerror("Database Error", str(exc))
            return

        cards_frame = tk.Frame(self.content, bg=BG)
        cards_frame.pack(fill="x", padx=26, pady=4)
        card_values = [
            ("Total Areas", counts["Areas"], BLUE),
            ("Supply Records", counts["Water Supply"], CYAN),
            ("Water Issues", counts["Water Issues"], ORANGE),
            ("Interrupted Records", pending, RED),
        ]
        for idx, (title, value, color) in enumerate(card_values):
            card, _ = self.card(cards_frame, title, value, color)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 9, 0), pady=4)
            cards_frame.columnconfigure(idx, weight=1)

        info = tk.Frame(self.content, bg=BG)
        info.pack(fill="x", padx=26, pady=(7, 5))
        tk.Label(info, text=f"Average supply shortfall: {avg_delay} minutes",
                 bg=BG, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(side="left")
        insight = tk.Frame(self.content, bg="#EAF6FC", highlightbackground="#B9DDF0", highlightthickness=1)
        insight.pack(fill="x", padx=26, pady=(4, 8))
        total = max(int(counts["Water Supply"]), 1)
        pct = round(100 * int(pending) / total)
        tk.Label(insight, text=f"✦ INSIGHT  •  {pct}% of supply records are interrupted. Average supply shortfall is {avg_delay} minutes.",
                 bg="#EAF6FC", fg=TEXT, font=("Segoe UI", 10, "bold"), wraplength=900, justify="left").pack(anchor="w", padx=14, pady=12)
        tk.Button(info, text="↻  Refresh Dashboard", command=self.refresh_current,
                  bg=GREEN, fg=WHITE, activebackground="#08764F", activeforeground=WHITE,
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=13, pady=8).pack(side="right")

        lower = tk.Frame(self.content, bg=BG)
        lower.pack(fill="both", expand=True, padx=26, pady=(8, 22))
        chart_box = tk.Frame(lower, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        chart_box.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(chart_box, text="Supply Status Overview", bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(13, 0))
        self.draw_status_chart(chart_box, compact=True)

        right = tk.Frame(lower, bg=WHITE, width=360, highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)
        tk.Label(right, text="Reliability Snapshot", bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(15, 12))
        try:
            top_area = query_rows("""
                SELECT a.area_name, COUNT(*) AS total
                FROM water_supply ws JOIN areas a ON a.area_id=ws.area_id
                WHERE ws.supply_status='Interrupted'
                GROUP BY a.area_id, a.area_name
                ORDER BY total DESC, a.area_name LIMIT 1
            """)
            issue_total = counts["Water Issues"]
            maintenance_open = query_rows("""
                SELECT COUNT(*) AS n FROM maintenance_records
                WHERE maintenance_status IN ('Pending','In Progress')
            """)[0]["n"]
            self.snapshot_row(right, "Most interrupted area",
                              f"{top_area[0]['area_name']} ({top_area[0]['total']})" if top_area else "No interruption")
            self.snapshot_row(right, "Total issue records", str(issue_total))
            self.snapshot_row(right, "Open maintenance", str(maintenance_open))
            self.snapshot_row(right, "Average shortfall", f"{avg_delay} min")
        except Error as exc:
            tk.Label(right, text=str(exc), bg=WHITE, fg=RED, wraplength=300).pack(padx=12)

        # Optional image banner, kept in the lower right area if file is present.
        try:
            from pathlib import Path
            img_path = Path(__file__).with_name("water_banner.png")
            if img_path.exists():
                self.banner_image = tk.PhotoImage(file=str(img_path))
                # Subsample to fit without requiring Pillow.
                factor = max(1, (self.banner_image.width() + 299) // 300)
                image = self.banner_image.subsample(factor, factor)
                tk.Label(right, image=image, bg=WHITE).pack(padx=10, pady=(8, 12))
        except Exception:
            self.draw_water_banner(right)
        if not Path(__file__).with_name("water_banner.png").exists():
            self.draw_water_banner(right)

    def draw_water_banner(self, parent):
        """Draw a crisp built-in water illustration when no external banner is present."""
        banner = tk.Canvas(parent, height=112, bg="#E8F7FC", highlightthickness=0)
        banner.pack(fill="x", padx=12, pady=(10, 12))
        banner.update_idletasks()
        width = max(280, banner.winfo_width())
        banner.create_rectangle(0, 0, width, 112, fill="#E8F7FC", outline="")
        banner.create_oval(width-120, -65, width+45, 100, fill="#D0F0FA", outline="")
        banner.create_polygon(0, 78, width*.22, 67, width*.43, 82, width*.68, 67,
                              width, 78, width, 112, 0, 112, fill="#54BDD8", outline="")
        banner.create_polygon(0, 91, width*.25, 80, width*.48, 94, width*.73, 80,
                              width, 91, width, 112, 0, 112, fill="#138DBB", outline="")
        banner.create_text(18, 25, anchor="w", text="WATER • RELIABILITY • COMMUNITY",
                           fill=NAVY, font=("Segoe UI", 9, "bold"))
        banner.create_text(18, 48, anchor="w", text="Every drop counts",
                           fill=BLUE, font=("Segoe UI", 15, "bold"))
        banner.create_oval(width-66, 20, width-40, 54, fill="#FFFFFF", outline="")
        banner.create_polygon(width-53, 12, width-67, 36, width-53, 58, width-39, 36,
                              fill="#13B8D5", outline="")

    def snapshot_row(self, parent, label, value):
        row = tk.Frame(parent, bg="#F6FAFD")
        row.pack(fill="x", padx=13, pady=4)
        tk.Label(row, text=label, bg="#F6FAFD", fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(7, 1))
        tk.Label(row, text=value, bg="#F6FAFD", fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(0, 7))

    # ---------------------------- CRUD PAGES ----------------------------

    def render_crud(self, page):
        config = TABLE_CONFIG[page]
        self.page_heading(f"{page} Management", "Add, view, search, edit, and delete MySQL records.")

        toolbar = tk.Frame(self.content, bg=BG)
        toolbar.pack(fill="x", padx=26, pady=(0, 12))

        tk.Button(toolbar, text="+  Add New", command=lambda: self.open_record_form(page, None),
                  bg=BLUE, fg=WHITE, activebackground=CYAN, activeforeground=WHITE,
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=14, pady=9).pack(side="left")
        tk.Button(toolbar, text="✎  Edit Selected", command=lambda: self.edit_selected(page),
                  bg="#176B9B", fg=WHITE, activebackground=BLUE, activeforeground=WHITE,
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=14, pady=9).pack(side="left", padx=8)
        tk.Button(toolbar, text="Delete Selected", command=lambda: self.delete_selected(page),
                  bg=RED, fg=WHITE, activebackground="#B92F42", activeforeground=WHITE,
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=14, pady=9).pack(side="left")

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=25)
        search_entry.pack(side="left", padx=(20, 6), ipady=5)
        search_entry.bind("<Return>", lambda _e: self.load_table(page))
        tk.Button(toolbar, text="⌕ Search", command=lambda: self.load_table(page),
                  bg=NAVY, fg=WHITE, activebackground=BLUE, activeforeground=WHITE,
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=13, pady=8).pack(side="left")
        tk.Button(toolbar, text="↻ Refresh", command=lambda: self.refresh_table(page),
                  bg=GREEN, fg=WHITE, activebackground="#08764F", activeforeground=WHITE,
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=13, pady=8).pack(side="right")

        table_wrap = tk.Frame(self.content, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        table_wrap.pack(fill="both", expand=True, padx=26, pady=(0, 24))
        self.tree = ttk.Treeview(table_wrap, show="headings", selectmode="browse")
        yscroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))
        yscroll.grid(row=0, column=1, sticky="ns", pady=(10, 0), padx=(0, 10))
        xscroll.grid(row=1, column=0, sticky="ew", padx=(10, 0), pady=(0, 10))
        table_wrap.rowconfigure(0, weight=1)
        table_wrap.columnconfigure(0, weight=1)
        self.load_table(page)

    def load_table(self, page):
        config = TABLE_CONFIG[page]
        try:
            sql = f"SELECT * FROM {config['table']}"
            params = []
            term = self.search_var.get().strip() if hasattr(self, "search_var") else ""
            if term:
                searchable = config["search"]
                sql += " WHERE " + " OR ".join([f"CAST({col} AS CHAR) LIKE %s" for col in searchable])
                params = [f"%{term}%"] * len(searchable)
            sql += f" ORDER BY {config['pk']} ASC"
            rows = query_rows(sql, tuple(params))
        except Error as exc:
            messagebox.showerror("Load Error", str(exc))
            return

        self.tree.delete(*self.tree.get_children())
        columns = [item[0] for item in config["columns"]]
        self.tree["columns"] = columns
        for col, label, _kind in config["columns"]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=145 if col not in ("issue_description",) else 270,
                             minwidth=90, anchor="w", stretch=True)
        for row in rows:
            values = []
            for col in columns:
                val = row.get(col)
                values.append("" if val is None else str(val))
            self.tree.insert("", "end", iid=str(row[config["pk"]]), values=values)
        self.tree.tag_configure("odd", background="#F5F9FD")
        self.tree.tag_configure("even", background=WHITE)
        for index, iid in enumerate(self.tree.get_children()):
            self.tree.item(iid, tags=("odd" if index % 2 else "even",))

    def refresh_table(self, page):
        self.search_var.set("")
        self.load_table(page)

    def edit_selected(self, page):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select a Record", "Please select a row to edit.")
            return
        config = TABLE_CONFIG[page]
        pk = config["pk"]
        try:
            rows = query_rows(f"SELECT * FROM {config['table']} WHERE {pk}=%s", (selected[0],))
            if rows:
                self.open_record_form(page, rows[0])
        except Error as exc:
            messagebox.showerror("Edit Error", str(exc))

    def delete_selected(self, page):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select a Record", "Please select a row to delete.")
            return
        config = TABLE_CONFIG[page]
        record_id = selected[0]
        if not messagebox.askyesno("Confirm Delete", f"Delete selected {page} record ID {record_id}?\nThis action also changes MySQL data."):
            return
        try:
            execute_sql(f"DELETE FROM {config['table']} WHERE {config['pk']}=%s", (record_id,))
            messagebox.showinfo("Deleted", "Record deleted from MySQL successfully.")
            self.load_table(page)
        except Error as exc:
            messagebox.showerror(
                "Delete Failed",
                "MySQL could not delete this record. It may be referenced by another table.\n"
                "Delete dependent records first or keep the parent record.\n\n" + str(exc)
            )

    def open_record_form(self, page, existing):
        config = TABLE_CONFIG[page]
        editing = existing is not None
        win = tk.Toplevel(self.root)
        win.title(("Edit " if editing else "Add ") + page + " Record")
        win.configure(bg=WHITE)
        win.transient(self.root)
        win.grab_set()
        win.geometry("760x680")
        win.minsize(650, 520)

        title = "Update Record" if editing else "Add New Record"
        tk.Label(win, text=title, bg=NAVY, fg=WHITE, font=("Segoe UI", 15, "bold"),
                 padx=20, pady=16).pack(fill="x")
        canvas = tk.Canvas(win, bg=WHITE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        form = tk.Frame(canvas, bg=WHITE)
        form.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        form_window = canvas.create_window((0, 0), window=form, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(form_window, width=event.width))
        canvas.pack(side="left", fill="both", expand=True, padx=(18, 0), pady=12)
        scrollbar.pack(side="right", fill="y", pady=12, padx=(0, 8))

        entries = {}
        for row_index, (col, label, kind) in enumerate(config["columns"]):
            if kind == "readonly":
                continue
            tk.Label(form, text=label, bg=WHITE, fg=TEXT,
                     font=("Segoe UI", 9, "bold")).grid(row=row_index, column=0, sticky="w",
                                                       padx=8, pady=(9, 2))
            if kind in ("status", "severity", "maintenance_status"):
                options = {
                    "status": ["Normal", "Delayed", "Interrupted"],
                    "severity": ["Low", "Medium", "High"],
                    "maintenance_status": ["Pending", "In Progress", "Completed"],
                }[kind]
                widget = ttk.Combobox(form, values=options, state="readonly", font=("Segoe UI", 10))
                if editing:
                    widget.set(str(existing.get(col) or ""))
                else:
                    widget.set(options[0])
            else:
                widget = ttk.Entry(form, font=("Segoe UI", 10))
                if editing:
                    value = existing.get(col)
                    widget.insert(0, "" if value is None else str(value))
                elif kind == "date":
                    widget.insert(0, date.today().isoformat())
                elif kind == "date_optional":
                    widget.insert(0, date.today().isoformat())
                elif col == "population":
                    widget.insert(0, "10000")
                elif col == "scheduled_minutes":
                    widget.insert(0, "120")
                elif col == "actual_minutes":
                    widget.insert(0, "120")
                elif col == "interruption_minutes":
                    widget.insert(0, "0")
                elif col == "repair_minutes":
                    widget.insert(0, "0")
            widget.grid(row=row_index, column=1, sticky="ew", padx=8, pady=(9, 2), ipady=5)
            entries[col] = (widget, kind, label)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(0, minsize=245)

        def save_record():
            try:
                values = {}
                for col, (widget, kind, label) in entries.items():
                    raw = widget.get().strip()
                    if kind == "number":
                        values[col] = safe_int(raw, label)
                    elif kind == "date":
                        values[col] = validate_date(raw, label)
                    elif kind == "date_optional":
                        values[col] = validate_date(raw, label, allow_blank=True)
                    else:
                        if raw == "":
                            raise ValueError(f"{label} cannot be empty.")
                        values[col] = raw

                if page == "Water Supply":
                    if values["scheduled_minutes"] < 0 or values["actual_minutes"] < 0 or values["interruption_minutes"] < 0:
                        raise ValueError("Minutes cannot be negative.")
                    if values["supply_status"] not in ("Normal", "Delayed", "Interrupted"):
                        raise ValueError("Choose a valid supply status.")
                if page == "Areas" and values["population"] < 0:
                    raise ValueError("Population cannot be negative.")
                if page == "Maintenance" and values["repair_minutes"] < 0:
                    raise ValueError("Repair minutes cannot be negative.")

                if editing:
                    pk = config["pk"]
                    set_clause = ", ".join([f"{col}=%s" for col in values])
                    params = list(values.values()) + [existing[pk]]
                    execute_sql(f"UPDATE {config['table']} SET {set_clause} WHERE {pk}=%s", tuple(params))
                    messagebox.showinfo("Updated", "Record updated in MySQL successfully.", parent=win)
                else:
                    cols = list(values.keys())
                    placeholders = ", ".join(["%s"] * len(cols))
                    execute_sql(
                        f"INSERT INTO {config['table']} ({', '.join(cols)}) VALUES ({placeholders})",
                        tuple(values.values())
                    )
                    messagebox.showinfo("Saved", "New record saved to MySQL successfully.", parent=win)
                win.destroy()
                self.load_table(page)
            except ValueError as exc:
                messagebox.showwarning("Check Input", str(exc), parent=win)
            except Error as exc:
                messagebox.showerror(
                    "MySQL Save Error",
                    "The record was not saved. Check that referenced Area ID / Supply ID / Issue ID exists.\n\n" + str(exc),
                    parent=win
                )

        button_bar = tk.Frame(win, bg=WHITE)
        button_bar.pack(fill="x", padx=20, pady=(0, 16))
        tk.Button(button_bar, text="Save to MySQL", command=save_record, bg=BLUE, fg=WHITE,
                  activebackground=CYAN, activeforeground=WHITE, bd=0,
                  font=("Segoe UI", 10, "bold"), cursor="hand2", padx=18, pady=10).pack(side="left")
        tk.Button(button_bar, text="Cancel", command=win.destroy, bg="#E8EEF4", fg=TEXT,
                  activebackground="#D5E0E9", bd=0, font=("Segoe UI", 10),
                  cursor="hand2", padx=18, pady=10).pack(side="left", padx=8)

    # ---------------------------- CHARTS / ANALYTICS ----------------------------

    def draw_status_chart(self, parent, compact=False):
        rows = query_rows("""
            SELECT supply_status, COUNT(*) AS total
            FROM water_supply GROUP BY supply_status
            ORDER BY supply_status
        """)
        labels = [r["supply_status"] for r in rows]
        values = [r["total"] for r in rows]
        fig = Figure(figsize=(5.3, 3.2) if compact else (5.4, 3.5), dpi=95, facecolor=WHITE)
        ax = fig.add_subplot(111)
        if values and sum(values):
            colors = {"Normal": "#13A879", "Delayed": "#F2A52B", "Interrupted": "#E65362"}
            ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90,
                   colors=[colors.get(label, BLUE) for label in labels],
                   textprops={"fontsize": 9})
            ax.axis("equal")
        else:
            ax.text(0.5, 0.5, "No supply data available", ha="center", va="center")
            ax.axis("off")
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=5)

    def render_analytics(self):
        self.page_heading("Analytics & Insights", "Monthly shortage uses interruption minutes. Priority score = shortage minutes + 60 × interruptions + 120 × unresolved high-severity issues.")

        filters = tk.Frame(self.content, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        filters.pack(fill="x", padx=26, pady=(0, 12))
        tk.Label(filters, text="Zone", bg=WHITE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(14, 6), pady=12)
        zones = ["All Zones"] + [r["zone_name"] for r in query_rows("SELECT DISTINCT zone_name FROM areas ORDER BY zone_name")]
        zone_box = ttk.Combobox(filters, textvariable=self.filter_zone_var, values=zones,
                                state="readonly", width=18)
        zone_box.pack(side="left", padx=(0, 15), pady=10)
        tk.Label(filters, text="From (YYYY-MM-DD)", bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
        from_entry = ttk.Entry(filters, textvariable=self.date_from_var, width=13)
        from_entry.pack(side="left", padx=(0, 12), ipady=4)
        tk.Label(filters, text="To", bg=WHITE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
        to_entry = ttk.Entry(filters, textvariable=self.date_to_var, width=13)
        to_entry.pack(side="left", padx=(0, 12), ipady=4)
        tk.Button(filters, text="Apply Filter", command=self.apply_analytics_filter,
                  bg=BLUE, fg=WHITE, activebackground=CYAN, activeforeground=WHITE,
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=13, pady=8).pack(side="left", padx=4)
        tk.Button(filters, text="↻ Refresh", command=self.reset_analytics,
                  bg=GREEN, fg=WHITE, activebackground="#08764F", activeforeground=WHITE,
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2", padx=13, pady=8).pack(side="left", padx=4)

        try:
            params = []
            where = []
            zone = self.filter_zone_var.get()
            if zone and zone != "All Zones":
                where.append("a.zone_name=%s")
                params.append(zone)
            start = self.date_from_var.get().strip()
            end = self.date_to_var.get().strip()
            if start:
                validate_date(start, "From date")
                where.append("ws.supply_date >= %s")
                params.append(start)
            if end:
                validate_date(end, "To date")
                where.append("ws.supply_date <= %s")
                params.append(end)
            clause = (" WHERE " + " AND ".join(where)) if where else ""
            status_rows = query_rows("""
                SELECT ws.supply_status, COUNT(*) AS total
                FROM water_supply ws JOIN areas a ON a.area_id=ws.area_id
            """ + clause + " GROUP BY ws.supply_status", tuple(params))
            issue_rows = query_rows("""
                SELECT wi.issue_type, COUNT(*) AS total
                FROM water_issues wi
                JOIN water_supply ws ON ws.supply_id=wi.supply_id
                JOIN areas a ON a.area_id=ws.area_id
            """ + clause + " GROUP BY wi.issue_type ORDER BY total DESC", tuple(params))
            area_rows = query_rows("""
                SELECT a.area_name,
                       SUM(CASE WHEN ws.supply_status='Interrupted' THEN 1 ELSE 0 END) AS interrupted,
                       COUNT(*) AS total
                FROM water_supply ws JOIN areas a ON a.area_id=ws.area_id
            """ + clause + " GROUP BY a.area_id, a.area_name ORDER BY interrupted DESC, total DESC LIMIT 10", tuple(params))
            maint_rows = query_rows("""
                SELECT mr.maintenance_status, COUNT(*) AS total
                FROM maintenance_records mr
                JOIN water_issues wi ON wi.issue_id=mr.issue_id
                JOIN water_supply ws ON ws.supply_id=wi.supply_id
                JOIN areas a ON a.area_id=ws.area_id
            """ + clause.replace("ws.supply_date", "ws.supply_date").replace("a.zone_name", "a.zone_name") +
                " GROUP BY mr.maintenance_status", tuple(params))
            monthly_shortage = query_rows("""
                SELECT DATE_FORMAT(ws.supply_date, '%Y-%m') AS month,
                       SUM(COALESCE(ws.interruption_minutes, 0)) AS shortage_minutes
                FROM water_supply ws JOIN areas a ON a.area_id=ws.area_id
            """ + clause + " GROUP BY DATE_FORMAT(ws.supply_date, '%Y-%m') ORDER BY month", tuple(params))
            priority_rows = query_rows("""
                SELECT a.area_id, a.area_name,
                       COALESCE(SUM(ws.interruption_minutes), 0) AS shortage_minutes,
                       COALESCE(SUM(CASE WHEN ws.supply_status='Interrupted' THEN 1 ELSE 0 END), 0) AS interrupted_records,
                       (SELECT COUNT(*) FROM water_issues wi
                        JOIN water_supply wsi ON wsi.supply_id=wi.supply_id
                        WHERE wsi.area_id=a.area_id AND wi.severity='High'
                        AND NOT EXISTS (SELECT 1 FROM maintenance_records mr
                                        WHERE mr.issue_id=wi.issue_id AND mr.maintenance_status='Completed')) AS urgent_issues
                FROM areas a LEFT JOIN water_supply ws ON ws.area_id=a.area_id
            """ + clause + " GROUP BY a.area_id, a.area_name ORDER BY shortage_minutes DESC LIMIT 10", tuple(params))
            for item in priority_rows:
                item['priority_score'] = int(item['shortage_minutes'] or 0) + 60 * int(item['interrupted_records'] or 0) + 120 * int(item['urgent_issues'] or 0)
        except (Error, ValueError) as exc:
            messagebox.showerror("Analytics Filter Error", str(exc))
            return

        # Keep actionable insights visible on the Analytics page, above its charts.
        shortage_peak = max(monthly_shortage, key=lambda row: int(row["shortage_minutes"] or 0), default=None)
        top_priority = max(priority_rows, key=lambda row: int(row.get("priority_score", 0)), default=None)
        supply_total = sum(int(row["total"] or 0) for row in status_rows)
        interrupted_total = sum(int(row["total"] or 0) for row in status_rows
                                if row["supply_status"] == "Interrupted")
        reliability_pct = round(100 * (supply_total - interrupted_total) / supply_total, 1) if supply_total else 0.0

        insights = tk.Frame(self.content, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        insights.pack(fill="x", padx=26, pady=(0, 12))
        tk.Label(insights, text="KEY INSIGHTS", bg=WHITE, fg=BLUE,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        insight_tiles = tk.Frame(insights, bg=WHITE)
        insight_tiles.pack(fill="x", padx=8, pady=(0, 10))
        insight_values = [
            ("PEAK SHORTAGE MONTH", (f"{shortage_peak['month']}  •  {int(shortage_peak['shortage_minutes'] or 0):,} min"
                                     if shortage_peak else "No shortage data"), CYAN),
            ("FIRST MAINTENANCE PRIORITY", (f"{top_priority['area_name']}  •  score {top_priority['priority_score']}"
                                            if top_priority else "No area data"), RED),
            ("SUPPLY RELIABILITY", f"{reliability_pct}%  •  {interrupted_total} interrupted / {supply_total} records", GREEN),
        ]
        for idx, (label, value, color) in enumerate(insight_values):
            tile = tk.Frame(insight_tiles, bg="#F6FAFD", highlightbackground=BORDER, highlightthickness=1)
            tile.grid(row=0, column=idx, sticky="nsew", padx=5, pady=3)
            insight_tiles.columnconfigure(idx, weight=1)
            tk.Frame(tile, bg=color, width=4).pack(side="left", fill="y")
            body = tk.Frame(tile, bg="#F6FAFD")
            body.pack(side="left", fill="both", expand=True, padx=10, pady=9)
            tk.Label(body, text=label, bg="#F6FAFD", fg=MUTED,
                     font=("Segoe UI", 8, "bold")).pack(anchor="w")
            tk.Label(body, text=value, bg="#F6FAFD", fg=TEXT,
                     font=("Segoe UI", 10, "bold"), wraplength=320, justify="left").pack(anchor="w", pady=(4, 0))

        chart_area = tk.Frame(self.content, bg=BG)
        chart_area.pack(fill="both", expand=True, padx=26, pady=(0, 20))
        for row_index in range(3):
            chart_area.rowconfigure(row_index, weight=1, minsize=300)
        chart_area.columnconfigure(0, weight=1)
        chart_area.columnconfigure(1, weight=1)

        self.plot_donut(chart_area, "Supply Status Mix", [r["supply_status"] for r in status_rows],
                        [r["total"] for r in status_rows], 0, 0)
        self.plot_horizontal(chart_area, "Issues by Type", [r["issue_type"] for r in issue_rows],
                             [r["total"] for r in issue_rows], 0, 1, ORANGE)
        self.plot_bar(chart_area, "Monthly Water Shortage (minutes)", [r["month"] for r in monthly_shortage],
                      [int(r["shortage_minutes"] or 0) for r in monthly_shortage], 1, 0, CYAN, rotate=True)
        self.plot_bar(chart_area, "Maintenance Priority by Area (score)", [r["area_name"] for r in priority_rows],
                      [r["priority_score"] for r in priority_rows], 1, 1, RED, rotate=True)
        self.plot_bar(chart_area, "Interrupted Supply Records by Area", [r["area_name"] for r in area_rows],
                      [int(r["interrupted"] or 0) for r in area_rows], 2, 0, "#DF4C5A", rotate=True)
        self.plot_donut(chart_area, "Maintenance Status", [r["maintenance_status"] for r in maint_rows],
                        [r["total"] for r in maint_rows], 2, 1)

    def plot_bar(self, parent, title, labels, values, row, col, color, rotate=False):
        frame = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        frame.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0),
                   pady=(0 if row == 0 else 8, 0))
        tk.Label(frame, text=title, bg=WHITE, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=13, pady=(10, 0))
        fig = Figure(figsize=(5.1, 2.5), dpi=90, facecolor=WHITE)
        ax = fig.add_subplot(111)
        if labels:
            bars = ax.bar(labels, values, color=color, width=0.65)
            ax.bar_label(bars, fontsize=8, padding=2)
            ax.tick_params(axis="x", labelsize=8, rotation=30 if rotate else 0)
            ax.tick_params(axis="y", labelsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(axis="y", alpha=0.18)
            ax.set_axisbelow(True)
            if rotate:
                for label in ax.get_xticklabels():
                    label.set_ha("right")
        else:
            ax.text(0.5, 0.5, "No records match this filter", ha="center", va="center")
            ax.axis("off")
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def plot_donut(self, parent, title, labels, values, row, col):
        frame = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        frame.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0), pady=(0 if row == 0 else 8, 0))
        tk.Label(frame, text=title, bg=WHITE, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=13, pady=(10, 0))
        fig = Figure(figsize=(5.1, 2.5), dpi=90, facecolor=WHITE); ax = fig.add_subplot(111)
        if labels and sum(values):
            wedges, _, _ = ax.pie(values, autopct="%1.0f%%", startangle=90, pctdistance=.78,
                                  wedgeprops={"width": .4, "edgecolor": WHITE}, textprops={"fontsize": 8})
            ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(.5, -.1), ncol=3, frameon=False, fontsize=8)
            ax.axis("equal")
        else:
            ax.text(.5, .5, "No records match this filter", ha="center", va="center"); ax.axis("off")
        fig.tight_layout(); canvas=FigureCanvasTkAgg(fig, master=frame); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def plot_horizontal(self, parent, title, labels, values, row, col, color):
        frame = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        frame.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0), pady=(0 if row == 0 else 8, 0))
        tk.Label(frame, text=title, bg=WHITE, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=13, pady=(10, 0))
        fig=Figure(figsize=(5.1, 2.5), dpi=90, facecolor=WHITE); ax=fig.add_subplot(111)
        if labels:
            pairs=sorted(zip(labels, values), key=lambda item:item[1]); bars=ax.barh([x[0] for x in pairs], [x[1] for x in pairs], color=color)
            ax.bar_label(bars, padding=3, fontsize=8); ax.tick_params(labelsize=8)
            ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False); ax.grid(axis="x", alpha=.18); ax.set_axisbelow(True)
        else:
            ax.text(.5, .5, "No records match this filter", ha="center", va="center"); ax.axis("off")
        fig.tight_layout(); canvas=FigureCanvasTkAgg(fig, master=frame); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def apply_analytics_filter(self):
        self.clear_content()
        self.render_analytics()

    def reset_analytics(self):
        self.filter_zone_var.set("All Zones")
        self.date_from_var.set("")
        self.date_to_var.set("")
        self.apply_analytics_filter()


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        available = style.theme_names()
        if "clam" in available:
            style.theme_use("clam")
        style.configure("TEntry", padding=5)
        style.configure("TCombobox", padding=4)
        style.configure(
            "Treeview",
            background=WHITE,
            fieldbackground=WHITE,
            foreground=TEXT,
            rowheight=30,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background="#E5EEF7",
            foreground=NAVY,
            font=("Segoe UI", 9, "bold"),
            padding=8,
        )
        style.map("Treeview", background=[("selected", "#CDE8FF")], foreground=[("selected", NAVY)])
    except Exception:
        pass

    app = WaterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()