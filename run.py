#!/usr/bin/env python3
"""
HCN - Hygiene Care Novelty
Easy startup script
"""
import subprocess
import sys
import os

def check_mongo():
    try:
        from pymongo import MongoClient
        c = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        c.server_info()
        print("✅ MongoDB is running")
        return True
    except Exception as e:
        print(f"⚠️  MongoDB not found: {e}")
        print("   Please start MongoDB: mongod --dbpath /data/db")
        print("   Or install MongoDB Compass and connect to localhost:27017")
        return False

def install_deps():
    print("📦 Installing dependencies...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '-q'])
    print("✅ Dependencies installed")

if __name__ == '__main__':
    print("=" * 50)
    print("  HCN - Hygiene Care Novelty")
    print("  Premium Cleaning & Hygiene Solutions")
    print("=" * 50)

    # Install deps
    try:
        import flask
        import pymongo
    except ImportError:
        install_deps()

    # Check MongoDB
    mongo_ok = check_mongo()
    if not mongo_ok:
        print("\n⚠️  Starting without MongoDB (demo mode - data won't persist)")
        input("   Press Enter to continue anyway, or Ctrl+C to exit...")

    print("\n🚀 Starting HCN server...")
    print("   Store:  http://localhost:5000")
    print("   Admin:  http://localhost:5000/admin")
    print("\n   Press Ctrl+C to stop\n")

    from app import app
    import os
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, port=5000, host='0.0.0.0')
