git add .
git commit -m "暫存本地修改"
git pull origin main --rebase

git add diary_gui.py version.txt
git commit -m "add version file"
git push

git add .
git commit -m "你的更新說明"
git pull origin main --rebase
git push
