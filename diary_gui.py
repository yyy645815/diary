import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict

from tkcalendar import DateEntry
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk



import requests   # 用來從 GitHub 抓版本號

# ---------- 版本資訊 ----------
# 本機程式版本號（更新程式時請同步修改這一行 & GitHub 的 version.txt）
APP_VERSION = "v1.1.1"

# 你的 GitHub 版本檔（raw）網址
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/yyy645815/diary/main/version.txt"


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

        # 自動儲存用計時器 & 最後儲存時間
        self.save_timer = None
        self.last_save_time: datetime | None = None
        self.status_label = None  # 之後在 build_ui 裡會建立

        # 建立介面
        self.build_ui()

         # ★ 開啟程式自動讀取既有資料
        self.load_from_file()

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

        # 原本的文字輸入框
        self.entry_date = ttk.Entry(date_row, width=15)
        self.entry_date.pack(side="left")

        # ★ 新增：可點選的小日曆
        self.date_picker = DateEntry(
            date_row,
            width=12,
            date_pattern="yyyy-mm-dd"  # 讓格式直接是 2025-11-09 這種
        )
        self.date_picker.pack(side="left", padx=5)

        # 選到日期時觸發事件
        self.date_picker.bind("<<DateEntrySelected>>", self.on_pick_date)


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

        # ★ 綁定輸入事件，觸發自動儲存
        self.entry_mood.bind("<KeyRelease>", self.schedule_auto_save)
        self.text_content.bind("<KeyRelease>", self.schedule_auto_save)
        # 也可以綁日期（例如手動改日期時）
        self.entry_date.bind("<FocusOut>", self.schedule_auto_save)

        # --- 下方按鈕列 ---
        btn_frame = ttk.Frame(self.root, padding=5)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="we")

        ttk.Button(btn_frame, text="今天新日記", command=self.new_today).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="新日記（指定日期）", command=self.new_custom_date).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="儲存本篇", command=self.save_current_entry).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="刪除這篇", command=self.delete_current_entry).pack(side="left", padx=2)
        # ★ 新增：重新整理日期列表按鈕
        ttk.Button(btn_frame, text="重新整理列表", command=self.refresh_listbox).pack(side="left", padx=2)

        # 右側：檢查更新 + 存取檔案
        ttk.Button(btn_frame, text="檢查更新", command=self.check_update).pack(side="right", padx=2)
        ttk.Button(btn_frame, text="讀取檔案", command=self.load_from_file).pack(side="right", padx=2)
        ttk.Button(btn_frame, text="儲存到檔案", command=self.save_to_file).pack(side="right", padx=2)

        # 左下角顯示版本與最後自動儲存時間
        ttk.Label(btn_frame, text=f"版本：{APP_VERSION}").pack(side="left", padx=10)
        self.status_label = ttk.Label(btn_frame, text="上次自動儲存：--:--")
        self.status_label.pack(side="left", padx=10)

        # 讓視窗可拉伸
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=3)
        self.root.rowconfigure(0, weight=1)

    # ---------- 狀態列更新 ----------

    def update_last_save_status(self):
        """更新狀態列顯示的『上次自動儲存時間』"""
        if self.status_label is None:
            return
        if self.last_save_time is None:
            self.status_label.config(text="上次自動儲存：--:--")
        else:
            # 只顯示時:分，例如 17:35
            t_str = self.last_save_time.strftime("%H:%M")
            self.status_label.config(text=f"上次自動儲存：{t_str}")

    # ---------- UI 操作邏輯 ----------

    def refresh_listbox(self):
        """更新左側日期列表顯示"""
        self.listbox.delete(0, tk.END)
        for date in sorted(self.diaries.keys()):
            e = self.diaries[date]
            first_line = e.內容.splitlines()[0] if e.內容 else ""
            if len(first_line) > 10:
                first_line = first_line[:10] + "..."
            self.listbox.insert(tk.END, f"{date}（{e.心情}） {first_line}")

    def on_select_date(self, event=None):
        """點選左邊日期時：先自動儲存目前內容，再載入新日期"""
        # 先試著自動存一下當前內容（靜默，不跳視窗）
        self.save_current_entry(silent=True)

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
        entry = self.diaries.get(date)
        if not entry:
            # 沒有這天，清空表單但保留日期
            self.clear_form()
            self.entry_date.insert(0, date)
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

    # ---------- 自動儲存邏輯 ----------

    def schedule_auto_save(self, event=None):
        """鍵盤輸入時呼叫：延遲 1 秒後自動儲存（防抖）"""
        if self.save_timer is not None:
            self.root.after_cancel(self.save_timer)
        # 1000 毫秒後執行靜默儲存
        self.save_timer = self.root.after(1000, lambda: self.save_current_entry(silent=True))

    # ---------- 日記操作 ----------

    def new_today(self):
        """今天新日記"""
        # 先靜默存目前內容
        self.save_current_entry(silent=True)
        self.clear_form()
        self.entry_date.insert(0, 今天字串())
        self.refresh_listbox()

    def new_custom_date(self):
        """指定日期新日記"""
        # 先靜默存目前內容
        self.save_current_entry(silent=True)
        self.refresh_listbox()

        d = simpledialog.askstring("指定日期", "請輸入日期（YYYY-MM-DD）：")
        if not d:
            return
        d = d.strip()
        if not 檢查日期格式(d):
            messagebox.showerror("錯誤", "日期格式錯誤，請用 YYYY-MM-DD。")
            return
        self.clear_form()
        self.entry_date.insert(0, d)

    def on_pick_date(self, event=None):
        """從右邊日曆選取日期時的處理"""
        # 先靜默存一下目前正在編輯的內容，避免遺失
        self.save_current_entry(silent=True)

        # 從 DateEntry 取得日期（datetime.date）
        d = self.date_picker.get_date()
        date_str = d.strftime("%Y-%m-%d")

        # 把日期填進文字框
        self.entry_date.delete(0, tk.END)
        self.entry_date.insert(0, date_str)

        # 如果這一天已有日記 → 直接載入
        if date_str in self.diaries:
            self.load_entry_to_form(date_str)
        else:
            # 沒有的話就當「新日記」，清空內容但保留日期
            self.clear_form()
            self.entry_date.insert(0, date_str)


    def save_current_entry(self, silent: bool = False):
            """
            儲存右邊正在編輯的這一篇
            silent=True 時不跳出成功/錯誤視窗（給自動儲存用）
            """
            date = self.entry_date.get().strip()
            mood = self.entry_mood.get().strip()
            content = self.text_content.get("1.0", tk.END).rstrip()

            # 沒日期就不存（自動儲存時安靜略過）
            if not date:
                if not silent:
                    messagebox.showerror("錯誤", "日期不能是空的。")
                return
            if not 檢查日期格式(date):
                if not silent:
                    messagebox.showerror("錯誤", "日期格式錯誤，請用 YYYY-MM-DD。")
                return
            if not mood:
                mood = "（未填心情）"

            # 更新內存資料
            self.diaries[date] = DiaryEntry(日期=date, 心情=mood, 內容=content or "(空白)")

            # 🔧 只在「不是靜默模式」時才重畫列表
            if not silent:
                self.refresh_listbox()

            # 寫入 JSON 檔，順便更新「上次自動儲存時間」
            self._write_json()

            if not silent:
                messagebox.showinfo("成功", f"{date} 的日記已儲存。")

    def delete_current_entry(self):
        """刪除目前日期欄位所代表的日記"""
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
        self._write_json()
        messagebox.showinfo("已刪除", f"{date} 的日記已刪除。")

    # ---------- 檔案 I/O ----------

    def _write_json(self):
        """實際將 self.diaries 寫入 JSON 檔（不跳視窗）"""
        data = [asdict(e) for e in self.diaries.values()]
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # 更新最後儲存時間 & 狀態列
        self.last_save_time = datetime.now()
        self.update_last_save_status()

    def save_to_file(self):
        """手動存檔按鈕：會顯示提示"""
        self._write_json()
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

    # ---------- 檢查更新 ----------

    def check_update(self):
        """到 GitHub 抓 version.txt，比對是否有新版本"""
        try:
            resp = requests.get(GITHUB_VERSION_URL, timeout=5)
            resp.raise_for_status()
            latest = resp.text.strip()
        except Exception as e:
            messagebox.showerror("錯誤", f"無法取得線上版本資訊：\n{e}")
            return

        if latest == APP_VERSION:
            messagebox.showinfo("版本檢查", f"目前已是最新版本：{APP_VERSION}")
        else:
            messagebox.showinfo(
                "有新版本！",
                f"目前版本：{APP_VERSION}\n"
                f"最新版本：{latest}\n\n"
                "請到 GitHub 下載最新版程式：\n"
                "https://github.com/yyy645815/diary"
            )


# ---------- 程式進入點 ----------

def main():
    root = tk.Tk()
    app = DiaryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
