📝 Diary GUI 日記程式

一個使用 Python + Tkinter 製作的簡易圖形化日記程式。
支援離線記錄、心情分類、JSON 儲存、以及 GitHub 自動檢查版本更新 功能。

🚀 功能介紹

📅 新增或修改每天的日記

💬 記錄心情與文字內容

💾 將日記儲存到 diary_gui.json

📤 從檔案重新讀取日記

🗑️ 刪除指定日期的日記

🔄 自動檢查 GitHub 上的最新版本

🌙 介面簡潔、支援中文介面

🧩 檔案結構
📁 diary/
├─ diary_gui.py        # 主程式
├─ version.txt         # GitHub 上的版本號檔案
├─ diary_gui.json      # 程式執行後自動產生的日記檔案
└─ README.md           # 專案說明文件

💻 執行方式

1️⃣ 安裝 Python（建議 3.10 以上）
2️⃣ 安裝所需模組：

pip install requests


3️⃣ 下載 diary_gui.py 並執行：

python diary_gui.py

🔄 檢查更新功能

此程式會自動從 GitHub 讀取版本資訊：

📄 version.txt

若版本不同，會提示「有新版本，請到 GitHub 下載」。

https://github.com/yyy645815/diary/

🌟 範例畫面（執行後）
📝 日記本（GUI 版 v1.0.0）
--------------------------------
📅 日期列表        | 右側輸入欄位
                   | 日期 / 心情 / 內容
                   | [儲存][刪除][檢查更新]

🧑‍💻 作者

開發者： @yyy645815

License：MIT
