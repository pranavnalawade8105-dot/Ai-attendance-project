"""FRONTEND: the window you see (Tkinter). Run with:  python main.py"""
import csv
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, simpledialog, ttk

import database as db

ADMIN_PASSWORD = "admin123"  # change this

db.init_db()
root = tk.Tk()
root.title("AI Attendance App")
root.geometry("320x220")


def make_table(parent, columns):
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=110, anchor="center")
    tree.pack(fill="both", expand=True, padx=8, pady=8)
    tree.tag_configure("risk", foreground="red")
    return tree


def fill(tree, rows, risk_index=None):
    tree.delete(*tree.get_children())
    for row in rows:
        shown = row if risk_index is None else row[:risk_index]
        risky = risk_index is not None and row[risk_index]
        tree.insert("", "end", values=shown, tags=("risk",) if risky else ())


# ---------------- STUDENT VIEW ----------------
def open_student_window():
    sid = simpledialog.askstring("Student View", "Enter your Student ID:", parent=root)
    if not sid:
        return
    info = db.student_summary(sid.strip())
    if info is None:
        messagebox.showerror("Not found", "Student ID not found")
        return
    win = tk.Toplevel(root)
    win.title(info["name"])
    tk.Label(win, text=f"{info['name']} ({info['student_id']})", font=("Arial", 14, "bold")).pack(pady=5)
    tk.Label(win, text=f"Present {info['present']} of {info['total']} days  |  {info['percentage']}%").pack()
    if info["at_risk"]:
        tk.Label(win, text="Warning: attendance below 75%!", fg="red").pack()
    tree = make_table(win, ("Date", "Status"))
    fill(tree, info["records"])


# ---------------- ADMIN ----------------
def open_admin_window():
    pw = simpledialog.askstring("Admin Login", "Password:", show="*", parent=root)
    if pw is None:
        return
    if pw != ADMIN_PASSWORD:
        messagebox.showerror("Login failed", "Wrong password")
        return

    win = tk.Toplevel(root)
    win.title("Admin Panel")
    win.geometry("560x420")
    tabs = ttk.Notebook(win)
    tabs.pack(fill="both", expand=True)

    # --- Tab 1: add student
    t1 = ttk.Frame(tabs)
    tabs.add(t1, text="Add Student")
    id_var, name_var = tk.StringVar(), tk.StringVar()
    ttk.Label(t1, text="Student ID").pack(pady=(20, 2))
    ttk.Entry(t1, textvariable=id_var).pack()
    ttk.Label(t1, text="Student Name").pack(pady=(10, 2))
    ttk.Entry(t1, textvariable=name_var).pack()

    def add():
        ok, msg = db.add_student(id_var.get(), name_var.get())
        (messagebox.showinfo if ok else messagebox.showerror)("Add Student", msg)
        if ok:
            id_var.set("")
            name_var.set("")

    ttk.Button(t1, text="Add", command=add).pack(pady=15)

    # --- Tab 2: mark attendance
    t2 = ttk.Frame(tabs)
    tabs.add(t2, text="Mark Attendance")
    pick, day, status = tk.StringVar(), tk.StringVar(value=str(date.today())), tk.StringVar(value="Present")
    ttk.Label(t2, text="Student").pack(pady=(20, 2))
    box = ttk.Combobox(t2, textvariable=pick, state="readonly", width=30)
    box.pack()
    box.configure(postcommand=lambda: box.configure(
        values=[f"{i} - {n}" for i, n in db.get_students()]))
    ttk.Label(t2, text="Date (YYYY-MM-DD)").pack(pady=(10, 2))
    ttk.Entry(t2, textvariable=day).pack()
    ttk.Label(t2, text="Status").pack(pady=(10, 2))
    ttk.Combobox(t2, textvariable=status, values=["Present", "Absent"], state="readonly").pack()

    def save():
        if not pick.get():
            messagebox.showerror("Mark Attendance", "Pick a student first")
            return
        ok, msg = db.mark_attendance(pick.get().split(" - ")[0], day.get().strip(), status.get())
        (messagebox.showinfo if ok else messagebox.showerror)("Mark Attendance", msg)

    ttk.Button(t2, text="Save", command=save).pack(pady=15)

    # --- Tab 3: all records + CSV export
    t3 = ttk.Frame(tabs)
    tabs.add(t3, text="All Records")
    records_tree = make_table(t3, ("Date", "ID", "Name", "Status"))

    def refresh_records():
        fill(records_tree, db.all_records())

    def export_csv():
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="attendance.csv")
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "ID", "Name", "Status"])
                writer.writerows(db.all_records())
            messagebox.showinfo("Export", "Saved!")

    bar = ttk.Frame(t3)
    bar.pack(pady=(0, 8))
    ttk.Button(bar, text="Refresh", command=refresh_records).pack(side="left", padx=5)
    ttk.Button(bar, text="Export CSV", command=export_csv).pack(side="left", padx=5)
    refresh_records()

    # --- Tab 4: AI insights (red = below 75%)
    t4 = ttk.Frame(tabs)
    tabs.add(t4, text="AI Insights")
    insights_tree = make_table(t4, ("ID", "Name", "Present", "Total", "Attendance %"))

    def refresh_insights():
        fill(insights_tree, db.insights(), risk_index=5)

    ttk.Button(t4, text="Refresh", command=refresh_insights).pack(pady=(0, 8))
    refresh_insights()
    tabs.bind("<<NotebookTabChanged>>", lambda e: (refresh_records(), refresh_insights()))


# ---------------- MAIN MENU ----------------
ttk.Label(root, text="AI Attendance App", font=("Arial", 16, "bold")).pack(pady=20)
ttk.Button(root, text="Admin Login", width=22, command=open_admin_window).pack(pady=5)
ttk.Button(root, text="Student View", width=22, command=open_student_window).pack(pady=5)
root.mainloop()