@echo off
chcp 65001 >nul
echo =====================================
echo 🚀🚀🚀 一鍵上傳 GitHub 開始！🚀🚀🚀
echo =====================================
echo.

:: 確認目前資料夾
cd /d "%~dp0"

:: 1️⃣ 加入所有變更
git add .
if errorlevel 1 (
    echo ❌ git add 發生錯誤！
    pause
    exit /b
)

:: 2️⃣ 自動建立 commit 訊息
set now=%date:~0,10%_%time:~0,8%
set now=%now::=-%
set now=%now: =_%
set now=%now:/=-%
git commit -m "自動上傳 %now%"
if %errorlevel% neq 0 (
    echo ⚠️ 目前沒有變更可提交，繼續進行。
) else (
    echo ✅ 已建立提交。
)
echo.

:: 3️⃣ 先同步遠端 main 分支
git pull origin main --rebase
if errorlevel 1 (
    echo ❌ 同步遠端失敗，請手動檢查！
    pause
    exit /b
)

:: 4️⃣ 推送到 GitHub
git push
if errorlevel 1 (
    echo ❌ 推送失敗，請檢查網路或登入狀態！
    pause
    exit /b
)

echo.
echo ===============================
echo ✅ 上傳完成！GitHub 已更新！
echo ===============================
pause
