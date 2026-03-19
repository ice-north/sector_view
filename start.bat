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

:: Python バージョンを表示
python --version

:: 必要パッケージをインストール（エラーは表示する）
echo.
echo 依存パッケージを確認・インストール中...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [エラー] パッケージのインストールに失敗しました。
    echo 上記のエラーメッセージを確認してください。
    pause
    exit /b 1
)

echo.
echo ============================================
echo  サーバーを起動します: http://localhost:5000
echo  終了するには Ctrl+C を押してください
echo ============================================
echo.

:: ブラウザを自動で開く（5秒待ってから）
start /b cmd /c "timeout /t 5 > nul && start http://localhost:5000"

python server.py
if errorlevel 1 (
    echo.
    echo [エラー] サーバーが起動できませんでした。
    echo 上記のエラーメッセージを確認してください。
)
pause
