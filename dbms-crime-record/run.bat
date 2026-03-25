@echo off
echo =============================================
echo  Crime Record Management System
echo =============================================
echo.
echo Installing dependencies...
C:/Python313/python.exe -m pip install Flask Werkzeug --quiet
echo.
echo Starting server at http://127.0.0.1:5000
echo Press Ctrl+C to stop.
echo.
C:/Python313/python.exe app.py
pause
