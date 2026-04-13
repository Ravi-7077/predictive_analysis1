#!/usr/bin/env python
"""
Power Prediction Digital Twin - Test Client
Tests the model server API with various scenarios
"""

import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:5000"
PREDICT_ENDPOINT = f"{BASE_URL}/predict"

# Test scenarios
TEST_SCENARIOS = [
    {
        "name": "Morning in Summer (Low Load)",
        "data": {
            "power_lag_1": 30,
            "power_lag_24": 32,
            "hour": 6,
            "dayofweek": 2,
            "month": 7,
            "temperature_2m": 22,
            "relative_humidity_2m": 65,
            "wind_speed_10m": 5,
            "wind_direction_10m": 90
        }
    },
    {
        "name": "Afternoon in Summer (High Load)",
        "data": {
            "power_lag_1": 85,
            "power_lag_24": 82,
            "hour": 14,
            "dayofweek": 3,
            "month": 7,
            "temperature_2m": 32,
            "relative_humidity_2m": 45,
            "wind_speed_10m": 8,
            "wind_direction_10m": 180
        }
    },
    {
        "name": "Evening in Winter (Peak Load)",
        "data": {
            "power_lag_1": 95,
            "power_lag_24": 98,
            "hour": 18,
            "dayofweek": 4,
            "month": 1,
            "temperature_2m": 5,
            "relative_humidity_2m": 80,
            "wind_speed_10m": 12,
            "wind_direction_10m": 270
        }
    },
    {
        "name": "Night Load (Stable)",
        "data": {
            "power_lag_1": 45,
            "power_lag_24": 43,
            "hour": 22,
            "dayofweek": 5,
            "month": 4,
            "temperature_2m": 18,
            "relative_humidity_2m": 70,
            "wind_speed_10m": 6,
            "wind_direction_10m": 45
        }
    },
    {
        "name": "Extreme Weather (High Wind)",
        "data": {
            "power_lag_1": 60,
            "power_lag_24": 58,
            "hour": 16,
            "dayofweek": 6,
            "month": 10,
            "temperature_2m": 15,
            "relative_humidity_2m": 85,
            "wind_speed_10m": 20,
            "wind_direction_10m": 180
        }
    }
]

def test_health():
    """Check if server is running"""
    try:
        response = requests.get(BASE_URL)
        print("✅ Server is running")
        return True
    except Exception as e:
        print(f"❌ Server not running: {e}")
        return False

def test_prediction(scenario):
    """Test a single prediction scenario"""
    try:
        start_time = time.time()
        response = requests.post(
            PREDICT_ENDPOINT,
            json=scenario["data"],
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n📊 {scenario['name']}")
            print(f"   Baseline Prediction: {result['baselinePred']:.2f} kW")
            print(f"   Hybrid Prediction:   {result['hybridPred']:.2f} kW")
            print(f"   Total Power:         {result['total']:.2f} kW")
            print(f"   Response Time:       {elapsed*1000:.1f}ms")
            return True
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Power Prediction Digital Twin - API Test Client")
    print("=" * 60)
    
    # Health check
    if not test_health():
        print("\nPlease start the server with: python model_server.py")
        return
    
    print("\n" + "=" * 60)
    print("Running Prediction Tests...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for scenario in TEST_SCENARIOS:
        if test_prediction(scenario):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed/(passed+failed)*100) if (passed+failed) > 0 else 0:.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    main()
