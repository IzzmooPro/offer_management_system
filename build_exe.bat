@echo off
echo ============================================================
echo   Teklif Yonetim Sistemi - EXE Build Script  (v1.0)
echo ============================================================
echo.

:: PyInstaller kontrolu
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [!] PyInstaller bulunamadi. Kuruluyor...
    pip install pyinstaller
    if errorlevel 1 (
        echo [HATA] PyInstaller kurulamadi.
        pause
        exit /b 1
    )
    echo [OK] PyInstaller kuruldu.
) else (
    echo [OK] PyInstaller mevcut.
)

echo.

:: Eski build ve dist klasorlerini temizle
echo [*] Eski build/dist klasorleri temizleniyor...
if exist build (
    rmdir /s /q build
    echo     build/ silindi.
)
if exist dist (
    rmdir /s /q dist
    echo     dist/ silindi.
)

echo.
echo [*] EXE derleniyor...
echo.

python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "TeklifYonetim" ^
    --icon "ico.ico" ^
    --add-data "assets;assets" ^
    --add-data "database/schema.sql;database" ^
    main.py

if errorlevel 1 (
    echo.
    echo [HATA] Derleme basarisiz. Yukaridaki ciktiyi inceleyin.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Build tamamlandi. EXE dosyasi dist klasorunde olusturuldu.
echo   Konum: dist\TeklifYonetim.exe
echo ============================================================
echo.
echo NOT: EXE dagitmadan once test verilerini temizleyin:
echo      python clear_for_distribution.py
echo.
pause
