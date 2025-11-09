import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

# ---------- 版本資訊 ----------
APP_VERSION = "v1.0.0"   # 想改版本號直接改這裡就好


# ---------- 資料結構 ----------

@dataclass
class DiaryEntry:
    日期: str      # "YYYY-MM-DD"
    心情: str
    內容: str


# ---------- 工具函式 ----------

def 今天字串() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def 檢查日期格式(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ---------- GUI 主程式 ----------

class DiaryApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        # 視窗標題顯示版本
        self.root.title(f"📝 日記本（GUI 版 {APP_VERSION}）")

        # 日記資料：用 dict 存，key = 日期
        self.diaries: Dict[str, DiaryEntry] = {}
        self.filename = "diary_gui.json"

        # 建立介面
        self.build_ui()

    def build_ui(self):
        # --- 左邊：日期列表 ---
        left_frame = ttk.Frame(self.root, padding=5)
        left_frame.grid(row=0, column=0, sticky="nswe")

        ttk.Label(left_frame, text="📅 日期列表").pack(anchor="w")

        self.listbox = tk.Listbox(left_frame, height=20)
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        self.listbox.bind("<<ListboxSelect>>", self.on_select_date)

        # --- 右邊：日記內容 ---
        right_frame = ttk.Frame(self.root, padding=5)
        right_frame.grid(row=0, column=1, sticky="nswe")

        # 日期
        date_row = ttk.Frame(right_frame)
        date_row.pack(fill="x", pady=2)
        ttk.Label(date_row, text="日期 (YYYY-MM-DD)：").pack(side="left")
        self.entry_date = ttk.Entry(date_row, width=15)
        self.entry_date.pack(side="left")

        # 心情
        mood_row = ttk.Frame(right_frame)
        mood_row.pack(fill="x", pady=2)
        ttk.Label(mood_row, text="心情：").pack(side="left")
        self.entry_mood = ttk.Entry(mood_row, width=20)
        self.entry_mood.pack(side="left")

        # 內容
        ttk.Label(right_frame, text="內容：").pack(anchor="w")
        self.text_content = tk.Text(right_frame, width=50, height=15)
        self.text_content.pack(fill="both", expand=True)

        # --- 下方按鈕列 ---
        btn_frame = ttk.Frame(self.root, padding=5)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="we")

        ttk.Button(btn_frame, text="今天新日記", command=self.new_today).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="新日記（指定日期）", command=self.new_custom_date).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="儲存本篇", command=self.save_current_entry).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="刪除這篇", command=self.delete_current_entry).pack(side="left", padx=2)

        ttk.Button(btn_frame, text="讀取檔案", command=self.load_from_file).pack(side="right", padx=2)
        ttk.Button(btn_frame, text="儲存到檔案", command=self.save_to_file).pack(side="right", padx=2)

        # 在按鈕列中顯示版本（左下角）
        ttk.Label(btn_frame, text=f"版本：{APP_VERSION}").pack(side="left", padx=10)

        # 調整 grid 權重，讓視窗可以拉伸
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=3)
        self.root.rowconfigure(0, weight=1)

    # ---------- UI 操作邏輯 ----------

    def refresh_listbox(self):
        """更新左側日期列表顯示"""
        self.listbox.delete(0, tk.END)
        for date in sorted(self.diaries.keys()):
            e = self.diaries[date]
            # 摘要用第一行
            first_line = e.內容.splitlines()[0] if e.內容 else ""
            if len(first_line) > 10:
                first_line = first_line[:10] + "..."
            self.listbox.insert(tk.END, f"{date}（{e.心情}） {first_line}")

    def on_select_date(self, event=None):
        """當使用者在 listbox 選擇某一天時，載入內容到右邊"""
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        dates = sorted(self.diaries.keys())
        if index >= len(dates):
            return
        date = dates[index]
        self.load_entry_to_form(date)

    def load_entry_to_form(self, date: str):
        """將指定日期的日記載入到右側編輯欄位"""
        entry = self.diaries.get(date)
        if not entry:
            return
        self.entry_date.delete(0, tk.END)
        self.entry_date.insert(0, entry.日期)
        self.entry_mood.delete(0, tk.END)
        self.entry_mood.insert(0, entry.心情)
        self.text_content.delete("1.0", tk.END)
        self.text_content.insert("1.0", entry.內容)

    def clear_form(self):
        self.entry_date.delete(0, tk.END)
        self.entry_mood.delete(0, tk.END)
        self.text_content.delete("1.0", tk.END)

    # ---------- 按鈕功能 ----------

    def new_today(self):
        """今天新日記：日期設為今天，清空內容"""
        self.clear_form()
        self.entry_date.insert(0, 今天字串())

    def new_custom_date(self):
        """新日記（指定日期）：彈出對話框問日期"""
        d = simpledialog.askstring("指定日期", "請輸入日期（YYYY-MM-DD）：")
        if not d:
            return
        d = d.strip()
        if not 檢查日期格式(d):
            messagebox.showerror("錯誤", "日期格式錯誤，請用 YYYY-MM-DD。")
            return
        self.clear_form()
        self.entry_date.insert(0, d)

    def save_current_entry(self):
        """儲存右邊正在編輯的這一篇"""
        date = self.entry_date.get().strip()
        mood = self.entry_mood.get().strip()
        content = self.text_content.get("1.0", tk.END).rstrip()

        if not date:
            messagebox.showerror("錯誤", "日期不能是空的。")
            return
        if not 檢查日期格式(date):
            messagebox.showerror("錯誤", "日期格式錯誤，請用 YYYY-MM-DD。")
            return
        if not mood:
            mood = "（未填心情）"

        self.diaries[date] = DiaryEntry(日期=date, 心情=mood, 內容=content or "(空白)")
        self.refresh_listbox()
        messagebox.showinfo("成功", f"{date} 的日記已儲存。")

    def delete_current_entry(self):
        """刪除目前右邊日期欄位代表的那一篇"""
        date = self.entry_date.get().strip()
        if not date:
            messagebox.showerror("錯誤", "請先在右邊輸入日期，或從左邊選一篇。")
            return
        if date not in self.diaries:
            messagebox.showwarning("提示", f"{date} 沒有日記可以刪。")
            return

        if not messagebox.askyesno("確認刪除", f"確定要刪除 {date} 的日記嗎？"):
            return

        del self.diaries[date]
        self.clear_form()
        self.refresh_listbox()
        messagebox.showinfo("已刪除", f"{date} 的日記已刪除。")

    def save_to_file(self):
        """把所有日記存到 JSON 檔"""
        data = [asdict(e) for e in self.diaries.values()]
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("儲存成功", f"已儲存到 {self.filename}")

    def load_from_file(self):
        """從 JSON 檔讀回日記"""
        if not os.path.exists(self.filename):
            messagebox.showwarning("提示", f"找不到 {self.filename}")
            return
        with open(self.filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.diaries = {d["日期"]: DiaryEntry(**d) for d in data}
        self.refresh_listbox()
        messagebox.showinfo("讀取成功", f"已從 {self.filename} 載入 {len(self.diaries)} 筆日記。")


# ---------- 程式進入點 ----------

def main():
    root = tk.Tk()
    app = DiaryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
