@echo off
echo Installing Python backend requirements...
echo.

echo Step 1: Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
echo.

echo Step 2: Installing Visual C++ build tools dependencies...
python -m pip install --upgrade setuptools-scm
echo.

echo Step 3: Installing core dependencies first...
python -m pip install fastapi==0.104.1
python -m pip install uvicorn[standard]==0.24.0
python -m pip install supabase==2.3.4
python -m pip install python-dotenv==1.0.0
python -m pip install python-multipart==0.0.6
echo.

echo Step 4: Installing authentication dependencies...
python -m pip install python-jose[cryptography]==3.3.0
python -m pip install passlib[bcrypt]==1.7.4
echo.

echo Step 5: Installing database dependencies...
python -m pip install asyncpg==0.29.0
python -m pip install pydantic==2.5.0
python -m pip install pydantic-settings==2.1.0
python -m pip install email-validator==2.1.0
echo.

echo Step 6: Installing image processing dependencies...
python -m pip install pillow==10.2.0
python -m pip install numpy==1.26.4
echo.

echo Step 7: Installing OpenCV (this may take a while)...
python -m pip install opencv-python==4.9.0.80
echo.

echo Step 8: Installing other dependencies...
python -m pip install pandas==2.1.4
python -m pip install requests==2.31.0
python -m pip install aiofiles==23.2.1
echo.

echo Step 9: Installing face recognition (this requires Visual C++)...
echo Note: If this fails, you may need to install Visual Studio Build Tools
python -m pip install cmake
python -m pip install dlib
python -m pip install face-recognition==1.3.0
echo.

echo Installation complete!
echo.
echo To start the server, run:
echo python main.py
pause
