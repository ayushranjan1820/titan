#!/usr/bin/env python3
"""
Test script for backend API endpoints.
Run this after starting the backend server.
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    print("🔍 Testing /health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check passed: {data}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_catalog_stats():
    """Test catalog stats endpoint."""
    print("\n🔍 Testing /catalog/stats endpoint...")
    try:
        response = requests.get(f"{API_BASE}/catalog/stats")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Catalog stats: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Catalog stats failed: {e}")
        return False


def test_products_list():
    """Test product listing endpoint."""
    print("\n🔍 Testing /products endpoint...")
    try:
        response = requests.get(f"{API_BASE}/products?limit=5")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Products list: Found {len(data)} products")
        if data:
            print(f"   Sample: {data[0]['name']}")
        return True
    except Exception as e:
        print(f"❌ Products list failed: {e}")
        return False


def test_products_filter():
    """Test product filtering."""
    print("\n🔍 Testing /products with filters...")
    try:
        response = requests.get(
            f"{API_BASE}/products",
            params={
                "max_price": 10000,
                "gender": "Men",
                "limit": 3
            }
        )
        response.raise_for_status()
        data = response.json()
        print(f"✅ Filtered products: Found {len(data)} products")
        return True
    except Exception as e:
        print(f"❌ Product filtering failed: {e}")
        return False


def test_chat_recommend():
    """Test chat recommendation endpoint."""
    print("\n🔍 Testing /chat/recommend endpoint...")
    try:
        response = requests.post(
            f"{API_BASE}/chat/recommend",
            json={
                "user_query": "I need a formal watch for a wedding under 10000"
            }
        )
        response.raise_for_status()
        data = response.json()
        print(f"✅ Chat recommendation:")
        print(f"   Understanding: {data['query_understanding']}")
        print(f"   Products found: {data['total_matches']}")
        print(f"   Recommended: {len(data['products'])}")
        print(f"   Explanation: {data['llm_explanation'][:100]}...")
        return True
    except Exception as e:
        print(f"❌ Chat recommendation failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Backend API Test Suite")
    print("=" * 60)
    print(f"\nTesting API at: {API_BASE}")
    print("Make sure the backend is running (uvicorn app.main:app --reload)\n")
    
    tests = [
        test_health,
        test_catalog_stats,
        test_products_list,
        test_products_filter,
        test_chat_recommend,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
