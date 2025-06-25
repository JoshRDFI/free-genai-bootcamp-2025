#!/usr/bin/env python3
"""
Test script to check if all required services are running and accessible.
"""

import requests
import json
import os
import sys

def test_service(name, url, endpoint="/", timeout=5):
    """Test if a service is accessible"""
    try:
        full_url = f"{url}{endpoint}"
        print(f"Testing {name} at {full_url}...")
        response = requests.get(full_url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {name} is accessible (status: {response.status_code})")
            return True
        else:
            print(f"❌ {name} returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} is not accessible (connection refused)")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {name} timed out")
        return False
    except Exception as e:
        print(f"❌ {name} error: {str(e)}")
        return False

def test_ollama_health():
    """Test Ollama health endpoint"""
    try:
        url = "http://localhost:11434/api/tags"
        print(f"Testing Ollama at {url}...")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama is accessible with {len(models)} models")
            for model in models:
                print(f"   - {model.get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama error: {str(e)}")
        return False

def test_flask_server():
    """Test Flask server health"""
    try:
        url = "http://localhost:8001/api/health"
        print(f"Testing Flask server at {url}...")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Flask server is accessible (status: {response.status_code})")
            return True
        else:
            print(f"❌ Flask server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Flask server error: {str(e)}")
        return False

def main():
    print("🔍 Testing Visual Novel Services...")
    print("=" * 50)
    
    # Test core services
    services = [
        ("Flask Server", "http://localhost:8001", "/api/health"),
        ("Ollama", "http://localhost:11434", "/api/tags"),
        ("TTS Service", "http://localhost:9200", "/health"),
        ("ASR Service", "http://localhost:9300", "/health"),
        ("Image Generation", "http://localhost:9500", "/health"),
        ("Embeddings", "http://localhost:6000", "/health"),
    ]
    
    results = []
    
    # Test Flask server first
    flask_ok = test_flask_server()
    results.append(("Flask Server", flask_ok))
    
    # Test Ollama specifically
    ollama_ok = test_ollama_health()
    results.append(("Ollama", ollama_ok))
    
    # Test other services
    for name, url, endpoint in services[2:]:
        ok = test_service(name, url, endpoint)
        results.append((name, ok))
    
    print("\n" + "=" * 50)
    print("📊 Service Status Summary:")
    print("=" * 50)
    
    all_ok = True
    for name, ok in results:
        status = "✅ OK" if ok else "❌ FAILED"
        print(f"{name:20} {status}")
        if not ok:
            all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok:
        print("🎉 All services are running!")
    else:
        print("⚠️  Some services are not running. Check the errors above.")
        print("\nTo start missing services:")
        print("1. For Ollama: ollama serve")
        print("2. For Flask server: cd visual-novel/server && python app.py")
        print("3. For other services: Check opea-docker setup")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main()) 