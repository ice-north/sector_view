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
echo ブラウザで sector_galaxy_v4_30.html を開いてください。
echo 終了するには Ctrl+C を押してください。
echo.

python server.py
pause
