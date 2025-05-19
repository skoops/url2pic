
import requests
import sys
import time
import os
from datetime import datetime

class ScreenshotAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.screenshot_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.status_code != 204:  # No content
                    return success, response.json()
                return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_get_user_agents(self):
        """Test getting user agents"""
        return self.run_test("Get User Agents", "GET", "user-agents", 200)

    def test_get_resolutions(self):
        """Test getting resolutions"""
        return self.run_test("Get Resolutions", "GET", "resolutions", 200)

    def test_create_screenshot(self, url="https://example.com"):
        """Test creating a screenshot"""
        data = {
            "url": url,
            "desktop_resolution": "1920×1080",
            "mobile_resolution": "375×667",
            "desktop_user_agent": None,
            "mobile_user_agent": None
        }
        success, response = self.run_test("Create Screenshot", "POST", "screenshots", 200, data=data)
        if success and 'id' in response:
            self.screenshot_id = response['id']
            print(f"Created screenshot with ID: {self.screenshot_id}")
        return success, response

    def test_get_screenshots(self):
        """Test getting all screenshots"""
        return self.run_test("Get All Screenshots", "GET", "screenshots", 200)

    def test_get_screenshot(self):
        """Test getting a specific screenshot"""
        if not self.screenshot_id:
            print("❌ No screenshot ID available for testing")
            return False, {}
        return self.run_test("Get Screenshot by ID", "GET", f"screenshots/{self.screenshot_id}", 200)

    def test_get_screenshot_images(self):
        """Test getting screenshot images"""
        if not self.screenshot_id:
            print("❌ No screenshot ID available for testing")
            return False, {}
        
        success1, _ = self.run_test("Get Desktop Screenshot Image", "GET", f"screenshots/{self.screenshot_id}/desktop", 200)
        success2, _ = self.run_test("Get Mobile Screenshot Image", "GET", f"screenshots/{self.screenshot_id}/mobile", 200)
        
        return success1 and success2, {}

    def test_delete_screenshot(self):
        """Test deleting a screenshot"""
        if not self.screenshot_id:
            print("❌ No screenshot ID available for testing")
            return False, {}
        
        return self.run_test("Delete Screenshot", "DELETE", f"screenshots/{self.screenshot_id}", 200)

def main():
    # Get the backend URL from environment or use the one from frontend/.env
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://2ae0dbeb-9679-45ac-a8ca-a660d9887734.preview.emergentagent.com')
    api_url = f"{backend_url}/api"
    
    print(f"Testing API at: {api_url}")
    
    # Setup tester
    tester = ScreenshotAPITester(api_url)
    
    # Run tests
    tester.test_root_endpoint()
    tester.test_get_user_agents()
    tester.test_get_resolutions()
    
    # Create a screenshot
    create_success, _ = tester.test_create_screenshot()
    if not create_success:
        print("❌ Screenshot creation failed, stopping tests")
        return 1
    
    # Wait a bit for the screenshot to be processed
    print("Waiting for screenshot processing...")
    time.sleep(2)
    
    # Get screenshots
    tester.test_get_screenshots()
    tester.test_get_screenshot()
    tester.test_get_screenshot_images()
    
    # Delete the screenshot
    tester.test_delete_screenshot()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
