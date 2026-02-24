@echo off
chcp 65001 > nul
echo ============================================
echo  セクター株価リアルタイムサーバー
echo ============================================
echo.

:: Python がインストールされているか確認
python --version > nul 2>&1
if errorlevel 1 (
    echo [エラー] Python が見つかりません。
    echo https://www.python.org/ からインストールしてください。
    pause
    exit /b 1
)

:: 必要パッケージをインストール（未インストールの場合のみ）
echo 依存パッケージを確認中...
pip install -r requirements.txt -q

echo.
echo サーバーを起動します: http://localhost:5000
echo ブラウザが自動的に開きます。
echo 終了するには Ctrl+C を押してください。
echo.

:: ブラウザを自動で開く（3秒待ってから）
start /b cmd /c "timeout /t 3 > nul && start http://localhost:5000"

python server.py
pause
