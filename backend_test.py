#!/usr/bin/env python3
"""
Backend API Tests for Fridge-to-Recipe MVP
Tests all backend endpoints with real data and proper error handling.
"""

import os
import sys
import json
import base64
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/.env')

BASE_URL = os.getenv('NEXT_PUBLIC_BASE_URL')
if not BASE_URL:
    print("❌ ERROR: NEXT_PUBLIC_BASE_URL not found in .env")
    sys.exit(1)

API_BASE = f"{BASE_URL}/api"
print(f"🔗 Testing API at: {API_BASE}\n")

# Test results tracking
test_results = {
    'passed': 0,
    'failed': 0,
    'errors': []
}

def log_test(name, passed, message=""):
    """Log test result"""
    if passed:
        test_results['passed'] += 1
        print(f"✅ {name}")
        if message:
            print(f"   {message}")
    else:
        test_results['failed'] += 1
        test_results['errors'].append(f"{name}: {message}")
        print(f"❌ {name}")
        print(f"   {message}")
    print()

def fetch_and_encode_image():
    """Fetch a real food image from Unsplash and encode to base64"""
    try:
        print("📸 Fetching test image from Unsplash...")
        # Small food image from Unsplash
        image_url = "https://images.unsplash.com/photo-1550989460-0adf9ea622e2?w=400"
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Encode to base64
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{image_base64}"
        print(f"✅ Image fetched and encoded ({len(image_base64)} chars)\n")
        return data_url
    except Exception as e:
        print(f"❌ Failed to fetch image: {e}\n")
        return None

def test_vision_endpoint(image_data_url):
    """Test POST /api/vision endpoint"""
    print("=" * 60)
    print("TEST 1: POST /api/vision - Ingredient Detection")
    print("=" * 60)
    
    # Test 1a: Valid request with image
    try:
        print("Test 1a: Valid image upload...")
        response = requests.post(
            f"{API_BASE}/vision",
            json={"imageBase64": image_data_url},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            if 'id' not in data:
                log_test("Vision - Valid Request", False, "Missing 'id' in response")
            elif 'ingredients' not in data:
                log_test("Vision - Valid Request", False, "Missing 'ingredients' in response")
            elif not isinstance(data['ingredients'], list):
                log_test("Vision - Valid Request", False, "'ingredients' is not an array")
            elif len(data['ingredients']) == 0:
                log_test("Vision - Valid Request", False, "ingredients array is empty")
            else:
                # Verify ingredient structure
                ingredient = data['ingredients'][0]
                required_fields = ['name', 'category', 'quantity', 'freshness', 'confidence']
                missing_fields = [f for f in required_fields if f not in ingredient]
                
                if missing_fields:
                    log_test("Vision - Valid Request", False, f"Ingredient missing fields: {missing_fields}")
                elif not isinstance(ingredient['confidence'], (int, float)):
                    log_test("Vision - Valid Request", False, f"confidence is not a number: {type(ingredient['confidence'])}")
                else:
                    log_test("Vision - Valid Request", True, 
                            f"Detected {len(data['ingredients'])} ingredients. First: {ingredient['name']} ({ingredient['category']})")
        else:
            log_test("Vision - Valid Request", False, 
                    f"Expected 200, got {response.status_code}: {response.text[:200]}")
    except requests.Timeout:
        log_test("Vision - Valid Request", False, "Request timed out (>60s)")
    except Exception as e:
        log_test("Vision - Valid Request", False, f"Exception: {str(e)}")
    
    # Test 1b: Error path - empty body
    try:
        print("Test 1b: Error handling - empty body...")
        response = requests.post(
            f"{API_BASE}/vision",
            json={},
            timeout=10
        )
        
        if response.status_code == 400:
            data = response.json()
            if 'error' in data and 'imageBase64' in data['error']:
                log_test("Vision - Error Handling", True, "Correctly returns 400 with error message")
            else:
                log_test("Vision - Error Handling", False, f"400 but unexpected error format: {data}")
        else:
            log_test("Vision - Error Handling", False, f"Expected 400, got {response.status_code}")
    except Exception as e:
        log_test("Vision - Error Handling", False, f"Exception: {str(e)}")

def test_recipes_endpoint():
    """Test POST /api/recipes endpoint"""
    print("=" * 60)
    print("TEST 2: POST /api/recipes - Recipe Generation")
    print("=" * 60)
    
    # Test 2a: Valid request
    try:
        print("Test 2a: Valid recipe generation request...")
        payload = {
            "ingredients": [
                {"name": "eggs", "category": "dairy"},
                {"name": "tomatoes", "category": "produce"},
                {"name": "bread", "category": "pantry"},
                {"name": "cheese", "category": "dairy"},
                {"name": "onion", "category": "produce"}
            ],
            "preferences": {
                "cuisine": "Italian",
                "diet": ["Vegetarian"],
                "allergies": "",
                "maxTime": 30,
                "servings": 2,
                "skill": "Home cook"
            }
        }
        
        response = requests.post(
            f"{API_BASE}/recipes",
            json=payload,
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            if 'id' not in data:
                log_test("Recipes - Valid Request", False, "Missing 'id' in response")
            elif 'recipes' not in data:
                log_test("Recipes - Valid Request", False, "Missing 'recipes' in response")
            elif not isinstance(data['recipes'], list):
                log_test("Recipes - Valid Request", False, "'recipes' is not an array")
            elif len(data['recipes']) != 3:
                log_test("Recipes - Valid Request", False, f"Expected exactly 3 recipes, got {len(data['recipes'])}")
            else:
                # Verify recipe structure
                recipe = data['recipes'][0]
                required_fields = [
                    'title', 'description', 'cuisine', 'difficulty', 
                    'prep_time_min', 'cook_time_min', 'servings',
                    'calories_per_serving', 'protein_g', 'carbs_g', 'fat_g',
                    'ingredients', 'missing_ingredients', 'equipment', 
                    'steps', 'chef_tips', 'pairs_with'
                ]
                missing_fields = [f for f in required_fields if f not in recipe]
                
                if missing_fields:
                    log_test("Recipes - Valid Request", False, f"Recipe missing fields: {missing_fields}")
                elif not isinstance(recipe['ingredients'], list) or len(recipe['ingredients']) == 0:
                    log_test("Recipes - Valid Request", False, "Recipe ingredients array is empty or not an array")
                elif not isinstance(recipe['steps'], list) or len(recipe['steps']) == 0:
                    log_test("Recipes - Valid Request", False, "Recipe steps array is empty or not an array")
                else:
                    # Verify ingredient structure in recipe
                    recipe_ing = recipe['ingredients'][0]
                    if 'name' not in recipe_ing or 'quantity' not in recipe_ing or 'have_it' not in recipe_ing:
                        log_test("Recipes - Valid Request", False, f"Recipe ingredient missing required fields: {recipe_ing}")
                    else:
                        # Store first recipe for favorites test
                        global saved_recipe
                        saved_recipe = data['recipes'][0]
                        log_test("Recipes - Valid Request", True, 
                                f"Generated 3 recipes. First: '{recipe['title']}' ({recipe['cuisine']}, {recipe['difficulty']})")
        else:
            log_test("Recipes - Valid Request", False, 
                    f"Expected 200, got {response.status_code}: {response.text[:200]}")
    except requests.Timeout:
        log_test("Recipes - Valid Request", False, "Request timed out (>90s)")
    except Exception as e:
        log_test("Recipes - Valid Request", False, f"Exception: {str(e)}")
    
    # Test 2b: Error path - empty ingredients
    try:
        print("Test 2b: Error handling - empty ingredients...")
        response = requests.post(
            f"{API_BASE}/recipes",
            json={"ingredients": []},
            timeout=10
        )
        
        if response.status_code == 400:
            data = response.json()
            if 'error' in data and 'ingredients' in data['error']:
                log_test("Recipes - Error Handling", True, "Correctly returns 400 with error message")
            else:
                log_test("Recipes - Error Handling", False, f"400 but unexpected error format: {data}")
        else:
            log_test("Recipes - Error Handling", False, f"Expected 400, got {response.status_code}")
    except Exception as e:
        log_test("Recipes - Error Handling", False, f"Exception: {str(e)}")

def test_favorites_crud():
    """Test Favorites CRUD operations"""
    print("=" * 60)
    print("TEST 3: Favorites CRUD Operations")
    print("=" * 60)
    
    if 'saved_recipe' not in globals():
        log_test("Favorites - CRUD", False, "No recipe available from previous test")
        return
    
    favorite_id = None
    
    # Test 3a: POST /api/favorites
    try:
        print("Test 3a: POST /api/favorites - Create favorite...")
        response = requests.post(
            f"{API_BASE}/favorites",
            json={"recipe": saved_recipe},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'id' not in data:
                log_test("Favorites - Create", False, "Missing 'id' in response")
                return
            else:
                favorite_id = data['id']
                log_test("Favorites - Create", True, f"Created favorite with id: {favorite_id}")
        else:
            log_test("Favorites - Create", False, f"Expected 200, got {response.status_code}: {response.text[:200]}")
            return
    except Exception as e:
        log_test("Favorites - Create", False, f"Exception: {str(e)}")
        return
    
    # Test 3b: GET /api/favorites - verify it's in the list
    try:
        print("Test 3b: GET /api/favorites - List favorites...")
        response = requests.get(
            f"{API_BASE}/favorites",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if not isinstance(data, list):
                log_test("Favorites - List", False, "Response is not an array")
            else:
                found = any(fav.get('id') == favorite_id for fav in data)
                if found:
                    log_test("Favorites - List", True, f"Found favorite {favorite_id} in list ({len(data)} total)")
                else:
                    log_test("Favorites - List", False, f"Favorite {favorite_id} not found in list")
        else:
            log_test("Favorites - List", False, f"Expected 200, got {response.status_code}")
    except Exception as e:
        log_test("Favorites - List", False, f"Exception: {str(e)}")
    
    # Test 3c: DELETE /api/favorites/:id
    try:
        print("Test 3c: DELETE /api/favorites/:id - Delete favorite...")
        response = requests.delete(
            f"{API_BASE}/favorites/{favorite_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok') == True:
                log_test("Favorites - Delete", True, f"Deleted favorite {favorite_id}")
            else:
                log_test("Favorites - Delete", False, f"Unexpected response: {data}")
        else:
            log_test("Favorites - Delete", False, f"Expected 200, got {response.status_code}")
    except Exception as e:
        log_test("Favorites - Delete", False, f"Exception: {str(e)}")
    
    # Test 3d: GET /api/favorites - verify it's gone
    try:
        print("Test 3d: GET /api/favorites - Verify deletion...")
        response = requests.get(
            f"{API_BASE}/favorites",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            found = any(fav.get('id') == favorite_id for fav in data)
            if not found:
                log_test("Favorites - Verify Deletion", True, f"Favorite {favorite_id} successfully removed")
            else:
                log_test("Favorites - Verify Deletion", False, f"Favorite {favorite_id} still in list after deletion")
        else:
            log_test("Favorites - Verify Deletion", False, f"Expected 200, got {response.status_code}")
    except Exception as e:
        log_test("Favorites - Verify Deletion", False, f"Exception: {str(e)}")

def test_404():
    """Test 404 for unknown routes"""
    print("=" * 60)
    print("TEST 4: 404 Handling")
    print("=" * 60)
    
    try:
        print("Test 4: GET /api/nonexistent - 404 handling...")
        response = requests.get(
            f"{API_BASE}/nonexistent",
            timeout=10
        )
        
        if response.status_code == 404:
            log_test("404 Handling", True, "Correctly returns 404 for unknown route")
        else:
            log_test("404 Handling", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test("404 Handling", False, f"Exception: {str(e)}")

def main():
    """Run all backend tests"""
    print("\n" + "=" * 60)
    print("🧪 FRIDGE-TO-RECIPE BACKEND API TESTS")
    print("=" * 60 + "\n")
    
    # Fetch test image
    image_data_url = fetch_and_encode_image()
    if not image_data_url:
        print("❌ Cannot proceed without test image")
        sys.exit(1)
    
    # Run all tests
    test_vision_endpoint(image_data_url)
    test_recipes_endpoint()
    test_favorites_crud()
    test_404()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"📈 Total:  {test_results['passed'] + test_results['failed']}")
    
    if test_results['failed'] > 0:
        print("\n❌ FAILED TESTS:")
        for error in test_results['errors']:
            print(f"  • {error}")
        sys.exit(1)
    else:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)

if __name__ == "__main__":
    main()
