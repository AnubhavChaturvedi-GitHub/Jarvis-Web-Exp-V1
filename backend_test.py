#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Jarvis AI Assistant
Tests all endpoints and command processing functionality
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class JarvisAPITester:
    def __init__(self, base_url="https://jarvis-assistant-24.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED {details}")
        else:
            self.failed_tests.append(f"{name}: {details}")
            print(f"❌ {name}: FAILED {details}")

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data}"
            self.log_test("Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'No message')}"
            self.log_test("Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_process_command(self, command: str, expected_action: str = None, expected_url: str = None):
        """Test command processing endpoint"""
        try:
            payload = {
                "command": command,
                "timestamp": datetime.utcnow().isoformat()
            }
            response = requests.post(f"{self.api_url}/process-command", json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Command: '{command}' -> Response: '{data.get('response', 'No response')}'"
                
                # Check expected action
                if expected_action:
                    if data.get('action') == expected_action:
                        details += f", Action: {data.get('action')} ✓"
                    else:
                        success = False
                        details += f", Expected action: {expected_action}, Got: {data.get('action')} ✗"
                
                # Check expected URL
                if expected_url:
                    if expected_url in str(data.get('url', '')):
                        details += f", URL contains: {expected_url} ✓"
                    else:
                        success = False
                        details += f", Expected URL to contain: {expected_url}, Got: {data.get('url')} ✗"
            else:
                details = f"Status: {response.status_code}, Command: '{command}'"
            
            self.log_test(f"Process Command", success, details)
            return success, response.json() if success else {}
        except Exception as e:
            self.log_test(f"Process Command", False, f"Command: '{command}', Exception: {str(e)}")
            return False, {}

    def test_command_history(self):
        """Test command history retrieval"""
        try:
            response = requests.get(f"{self.api_url}/commands", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Commands retrieved: {len(data)}"
            self.log_test("Command History", success, details)
            return success
        except Exception as e:
            self.log_test("Command History", False, f"Exception: {str(e)}")
            return False

    def run_website_opening_tests(self):
        """Test website opening commands"""
        print("\n🌐 Testing Website Opening Commands...")
        
        website_tests = [
            ("open youtube", "open_url", "youtube.com"),
            ("visit google", "open_url", "google.com"),
            ("go to facebook", "open_url", "facebook.com"),
            ("open twitter", "open_url", "twitter.com"),
            ("visit instagram", "open_url", "instagram.com"),
            ("go to linkedin", "open_url", "linkedin.com"),
            ("open github", "open_url", "github.com"),
            ("visit netflix", "open_url", "netflix.com"),
            ("go to amazon", "open_url", "amazon.com"),
        ]
        
        for command, expected_action, expected_url in website_tests:
            self.test_process_command(command, expected_action, expected_url)

    def run_search_tests(self):
        """Test search commands"""
        print("\n🔍 Testing Search Commands...")
        
        search_tests = [
            ("search for cats on youtube", "open_url", "youtube.com/results"),
            ("search for dogs on google", "open_url", "google.com/search"),
            ("google artificial intelligence", "open_url", "google.com/search"),
            ("search machine learning", "open_url", "google.com/search"),
        ]
        
        for command, expected_action, expected_url in search_tests:
            self.test_process_command(command, expected_action, expected_url)

    def run_greeting_tests(self):
        """Test greeting commands"""
        print("\n👋 Testing Greeting Commands...")
        
        greeting_tests = [
            "hello jarvis",
            "hi assistant", 
            "hey",
            "how are you",
            "good morning",
            "good afternoon",
            "good evening",
            "thank you",
            "what is your name",
        ]
        
        for command in greeting_tests:
            self.test_process_command(command)

    def run_time_tests(self):
        """Test time-related commands"""
        print("\n⏰ Testing Time Commands...")
        
        time_tests = [
            "what time is it",
            "current time",
            "what date is it",
            "current date",
        ]
        
        for command in time_tests:
            self.test_process_command(command)

    def run_error_handling_tests(self):
        """Test error handling with invalid commands"""
        print("\n❓ Testing Error Handling...")
        
        invalid_commands = [
            "invalid command xyz",
            "random gibberish",
            "unknown request",
        ]
        
        for command in invalid_commands:
            success, response = self.test_process_command(command)
            if success and response.get('success') == False:
                print(f"   ✓ Properly handled invalid command: '{command}'")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Jarvis AI Assistant Backend Tests")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity tests
        print("\n🔧 Testing Basic Endpoints...")
        self.test_health_endpoint()
        self.test_root_endpoint()
        
        # Command processing tests
        self.run_website_opening_tests()
        self.run_search_tests()
        self.run_greeting_tests()
        self.run_time_tests()
        self.run_error_handling_tests()
        
        # Command history test
        print("\n📚 Testing Command History...")
        self.test_command_history()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 TEST RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for failed_test in self.failed_tests:
                print(f"   • {failed_test}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = JarvisAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())