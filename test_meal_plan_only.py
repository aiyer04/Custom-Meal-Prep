#!/usr/bin/env python3
"""
Quick test for meal plan generation only
"""

import requests
import json
import time

BASE_URL = "https://nutriplan-app-7.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

def test_meal_plan_generation():
    # Register user
    timestamp = str(int(time.time()))
    username = f"testuser_{timestamp}"
    password = "testpass123"
    
    reg_data = {"username": username, "password": password}
    response = requests.post(f"{API_BASE}/auth/register", json=reg_data)
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create profile
    profile_data = {
        "gender": "male",
        "age": 30,
        "weight": 75.5,
        "height": 175.0,
        "activity_level": "moderately_active",
        "fitness_goal": "weight_loss",
        "calorie_target": 2000,
        "protein_target": 150,
        "fiber_target": 30,
        "dietary_restrictions": ["vegetarian"],
        "allergies": ["peanuts"]
    }
    
    requests.post(f"{API_BASE}/profile", json=profile_data, headers=headers)
    
    # Generate meal plan
    print("🤖 Generating meal plan...")
    response = requests.post(f"{API_BASE}/meal-plan/generate", headers=headers, timeout=60)
    
    if response.status_code == 200:
        print("✅ Meal plan generated successfully!")
        data = response.json()
        print(f"Meal plan ID: {data['meal_plan_id']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_meal_plan_generation()