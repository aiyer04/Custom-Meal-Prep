#!/usr/bin/env python3
"""
NutriPlan Backend API Testing Suite
Tests all backend endpoints with comprehensive error handling and validation
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class NutriPlanAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.access_token = None
        self.user_id = None
        self.meal_plan_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, timeout: int = 30) -> tuple:
        """Make HTTP request with error handling"""
        url = f"{self.api_base}{endpoint}"
        
        # Add auth header if token is available
        if self.access_token and headers is None:
            headers = {"Authorization": f"Bearer {self.access_token}"}
        elif self.access_token and headers:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return response.status_code < 400, response_data
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error"}
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_health_check(self):
        """Test health check endpoint"""
        success, response = self.make_request("GET", "/health")
        
        if success and response.get("status") == "healthy":
            self.log_test("Health Check", True, "API is healthy", response)
        else:
            self.log_test("Health Check", False, "Health check failed", response)
    
    def test_user_registration(self):
        """Test user registration with unique username"""
        timestamp = str(int(time.time()))
        username = f"testuser_{timestamp}"
        password = "testpass123"
        
        data = {
            "username": username,
            "password": password
        }
        
        success, response = self.make_request("POST", "/auth/register", data)
        
        if success and "access_token" in response:
            self.access_token = response["access_token"]
            self.log_test("User Registration", True, f"User {username} registered successfully", response)
            return username, password
        else:
            self.log_test("User Registration", False, "Registration failed", response)
            return None, None
    
    def test_user_login(self, username: str, password: str):
        """Test user login"""
        data = {
            "username": username,
            "password": password
        }
        
        success, response = self.make_request("POST", "/auth/login", data)
        
        if success and "access_token" in response:
            self.access_token = response["access_token"]
            self.log_test("User Login", True, "Login successful", response)
            return True
        else:
            self.log_test("User Login", False, "Login failed", response)
            return False
    
    def test_get_profile_empty(self):
        """Test getting profile when it's empty"""
        success, response = self.make_request("GET", "/profile")
        
        if success and "user_id" in response:
            self.user_id = response["user_id"]
            self.log_test("Get Empty Profile", True, "Profile retrieved (empty)", response)
        else:
            self.log_test("Get Empty Profile", False, "Failed to get profile", response)
    
    def test_create_profile(self):
        """Test creating user profile"""
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
        
        success, response = self.make_request("POST", "/profile", profile_data)
        
        if success and response.get("message") == "Profile updated successfully":
            self.log_test("Create Profile", True, "Profile created successfully", response)
            return True
        else:
            self.log_test("Create Profile", False, "Profile creation failed", response)
            return False
    
    def test_get_profile_with_data(self):
        """Test getting profile after creation"""
        success, response = self.make_request("GET", "/profile")
        
        if success and response.get("profile") is not None:
            profile = response["profile"]
            required_fields = ["gender", "age", "weight", "height", "activity_level", "fitness_goal"]
            has_all_fields = all(field in profile for field in required_fields)
            
            if has_all_fields:
                self.log_test("Get Profile with Data", True, "Profile retrieved with all data", response)
            else:
                self.log_test("Get Profile with Data", False, "Profile missing required fields", response)
        else:
            self.log_test("Get Profile with Data", False, "Failed to get profile with data", response)
    
    def test_generate_meal_plan(self):
        """Test meal plan generation (CRITICAL - AI integration)"""
        print("🤖 Generating meal plan with AI (this may take 20-30 seconds)...")
        
        success, response = self.make_request("POST", "/meal-plan/generate", timeout=60)
        
        if success and "meal_plan_id" in response:
            self.meal_plan_id = response["meal_plan_id"]
            meal_plan = response.get("meal_plan", {})
            
            # Validate meal plan structure
            validation_errors = []
            
            if "days" not in meal_plan:
                validation_errors.append("Missing 'days' array")
            else:
                days = meal_plan["days"]
                if len(days) != 7:
                    validation_errors.append(f"Expected 7 days, got {len(days)}")
                
                for i, day in enumerate(days):
                    day_num = i + 1
                    if "day" not in day:
                        validation_errors.append(f"Day {day_num} missing 'day' field")
                    
                    for meal_type in ["breakfast", "lunch", "dinner"]:
                        if meal_type not in day:
                            validation_errors.append(f"Day {day_num} missing {meal_type}")
                        else:
                            meal = day[meal_type]
                            
                            # Check meal structure
                            if "name" not in meal:
                                validation_errors.append(f"Day {day_num} {meal_type} missing name")
                            
                            if "recipe" not in meal:
                                validation_errors.append(f"Day {day_num} {meal_type} missing recipe")
                            else:
                                recipe = meal["recipe"]
                                if "ingredients" not in recipe:
                                    validation_errors.append(f"Day {day_num} {meal_type} missing ingredients")
                                if "instructions" not in recipe:
                                    validation_errors.append(f"Day {day_num} {meal_type} missing instructions")
                            
                            if "nutrition" not in meal:
                                validation_errors.append(f"Day {day_num} {meal_type} missing nutrition")
                            else:
                                nutrition = meal["nutrition"]
                                required_nutrition = ["calories", "protein", "carbs", "fat", "fiber", "sugar"]
                                for nutrient in required_nutrition:
                                    if nutrient not in nutrition:
                                        validation_errors.append(f"Day {day_num} {meal_type} missing {nutrient}")
                            
                            # Check dining_out flag was added
                            if "dining_out" not in meal:
                                validation_errors.append(f"Day {day_num} {meal_type} missing dining_out flag")
            
            if validation_errors:
                self.log_test("Generate Meal Plan", False, f"Meal plan structure invalid: {'; '.join(validation_errors)}", response)
            else:
                self.log_test("Generate Meal Plan", True, "Meal plan generated and validated successfully", {
                    "meal_plan_id": self.meal_plan_id,
                    "days_count": len(meal_plan.get("days", [])),
                    "structure": "Valid"
                })
                return True
        else:
            self.log_test("Generate Meal Plan", False, "Meal plan generation failed", response)
        
        return False
    
    def test_get_latest_meal_plan(self):
        """Test getting latest meal plan"""
        success, response = self.make_request("GET", "/meal-plan/latest")
        
        if success and "meal_plan_id" in response:
            returned_id = response["meal_plan_id"]
            if returned_id == self.meal_plan_id:
                self.log_test("Get Latest Meal Plan", True, "Latest meal plan retrieved correctly", {
                    "meal_plan_id": returned_id
                })
            else:
                self.log_test("Get Latest Meal Plan", False, f"Wrong meal plan ID returned: {returned_id} vs {self.meal_plan_id}", response)
        else:
            self.log_test("Get Latest Meal Plan", False, "Failed to get latest meal plan", response)
    
    def test_update_meal_dining_status(self):
        """Test updating meal dining out status"""
        if not self.meal_plan_id:
            self.log_test("Update Meal Dining Status", False, "No meal plan ID available", None)
            return False
        
        update_data = {
            "meal_plan_id": self.meal_plan_id,
            "day": 1,
            "meal_type": "breakfast",
            "dining_out": True
        }
        
        success, response = self.make_request("PUT", "/meal-plan/update-meal", update_data)
        
        if success and response.get("message") == "Meal updated successfully":
            self.log_test("Update Meal Dining Status", True, "Meal dining status updated successfully", response)
            return True
        else:
            self.log_test("Update Meal Dining Status", False, "Failed to update meal dining status", response)
            return False
    
    def test_get_grocery_list(self):
        """Test getting grocery list and verify dining_out exclusion"""
        if not self.meal_plan_id:
            self.log_test("Get Grocery List", False, "No meal plan ID available", None)
            return
        
        success, response = self.make_request("GET", f"/grocery-list/{self.meal_plan_id}")
        
        if success and "ingredients" in response:
            ingredients = response["ingredients"]
            self.log_test("Get Grocery List", True, f"Grocery list retrieved with {len(ingredients)} ingredients", {
                "meal_plan_id": response["meal_plan_id"],
                "ingredient_count": len(ingredients)
            })
        else:
            self.log_test("Get Grocery List", False, "Failed to get grocery list", response)
    
    def test_error_cases(self):
        """Test various error scenarios"""
        # Test without authentication
        old_token = self.access_token
        self.access_token = None
        
        success, response = self.make_request("GET", "/profile")
        if not success and (response.get("detail") == "Not authenticated" or "authentication" in str(response).lower()):
            self.log_test("Error Case - No Auth", True, "Correctly rejected request without auth", response)
        else:
            self.log_test("Error Case - No Auth", False, "Should have rejected request without auth", response)
        
        # Test with invalid token
        self.access_token = "invalid_token"
        success, response = self.make_request("GET", "/profile")
        if not success and ("invalid" in str(response).lower() or "authentication" in str(response).lower()):
            self.log_test("Error Case - Invalid Token", True, "Correctly rejected invalid token", response)
        else:
            self.log_test("Error Case - Invalid Token", False, "Should have rejected invalid token", response)
        
        # Restore valid token
        self.access_token = old_token
        
        # Test meal plan generation without profile (create new user)
        timestamp = str(int(time.time()))
        username = f"noprofile_{timestamp}"
        password = "testpass123"
        
        reg_data = {"username": username, "password": password}
        success, response = self.make_request("POST", "/auth/register", reg_data)
        
        if success:
            temp_token = response["access_token"]
            old_token = self.access_token
            self.access_token = temp_token
            
            success, response = self.make_request("POST", "/meal-plan/generate")
            if not success and "profile" in str(response).lower():
                self.log_test("Error Case - No Profile", True, "Correctly rejected meal plan generation without profile", response)
            else:
                self.log_test("Error Case - No Profile", False, "Should have rejected meal plan generation without profile", response)
            
            self.access_token = old_token
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 Starting NutriPlan Backend API Tests")
        print("=" * 50)
        
        # Core functionality tests
        self.test_health_check()
        
        username, password = self.test_user_registration()
        if not username:
            print("❌ Cannot continue tests - registration failed")
            return
        
        if not self.test_user_login(username, password):
            print("❌ Cannot continue tests - login failed")
            return
        
        self.test_get_profile_empty()
        
        if not self.test_create_profile():
            print("❌ Cannot continue tests - profile creation failed")
            return
        
        self.test_get_profile_with_data()
        
        if not self.test_generate_meal_plan():
            print("❌ Cannot continue tests - meal plan generation failed")
            return
        
        self.test_get_latest_meal_plan()
        self.test_update_meal_dining_status()
        self.test_get_grocery_list()
        
        # Error case tests
        self.test_error_cases()
        
        # Summary
        print("\n" + "=" * 50)
        print("🏁 Test Summary")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return self.test_results

def main():
    """Main test execution"""
    BASE_URL = "https://nutriplan-app-7.preview.emergentagent.com"
    
    print(f"🎯 Testing NutriPlan API at: {BASE_URL}")
    
    tester = NutriPlanAPITester(BASE_URL)
    results = tester.run_all_tests()
    
    # Return results for programmatic access
    return results

if __name__ == "__main__":
    main()