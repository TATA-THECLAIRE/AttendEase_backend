import subprocess
import sys

def install_asyncpg():
    """Install asyncpg for async database operations"""
    try:
        print("📦 Installing asyncpg for async database operations...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "asyncpg"])
        print("✅ asyncpg installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install asyncpg: {e}")
        return False

if __name__ == "__main__":
    install_asyncpg()
