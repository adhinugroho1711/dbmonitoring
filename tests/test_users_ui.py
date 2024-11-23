import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import HtmlTestRunner
import time

class TestUserManagementUI(unittest.TestCase):
    def setUp(self):
        # Initialize Chrome driver with options
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.implicitly_wait(10)
        # Start the Flask application (assuming it's running on default port)
        self.base_url = "http://127.0.0.1:5000"
        # Admin credentials
        self.admin_username = "admin"
        self.admin_password = "change-this-password"
        # Login before each test
        self.login()
        
    def tearDown(self):
        self.driver.quit()

    def login(self):
        """Helper method to login as admin"""
        self.driver.get(f"{self.base_url}/login")
        
        # Wait for login form and fill credentials
        username_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = self.driver.find_element(By.NAME, "password")
        
        username_field.send_keys(self.admin_username)
        password_field.send_keys(self.admin_password)
        
        # Submit login form
        password_field.submit()
        
        # Wait for successful login (redirect to dashboard)
        WebDriverWait(self.driver, 10).until(
            EC.url_to_be(f"{self.base_url}/")
        )

    def test_user_status_toggle(self):
        """Test the user status toggle functionality"""
        # Navigate to users page
        self.driver.get(f"{self.base_url}/users")
        
        # Wait for the table to be visible
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table"))
        )
        
        # Find a non-admin user's toggle button
        toggle_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[id^='toggle-btn-']")
        toggle_button = None
        for button in toggle_buttons:
            username = button.find_element(By.XPATH, "../../..").find_element(By.TAG_NAME, "td").text
            if username.lower() != "admin":
                toggle_button = button
                break
                
        if not toggle_button:
            self.skipTest("No non-admin users found to test status toggle")
            
        # Get initial status
        initial_status = toggle_button.find_element(By.TAG_NAME, "span").text
        
        # Click the toggle button
        toggle_button.click()
        
        # Handle the confirmation alert
        alert = WebDriverWait(self.driver, 10).until(EC.alert_is_present())
        alert.accept()
        
        # Wait for status to change
        time.sleep(2)  # Allow time for AJAX request to complete
        
        # Get new status
        new_status = toggle_button.find_element(By.TAG_NAME, "span").text
        
        # Verify status changed
        self.assertNotEqual(initial_status, new_status)
        self.assertTrue(new_status in ["Enable", "Disable"])

    def test_error_handling(self):
        """Test error handling when toggling admin user status"""
        self.driver.get(f"{self.base_url}/users")
        
        # Wait for the table to be visible
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table"))
        )
        
        # Find admin user's row
        rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        admin_row = None
        for row in rows:
            if row.find_element(By.TAG_NAME, "td").text.lower() == "admin":
                admin_row = row
                break
                
        if not admin_row:
            self.skipTest("Admin user not found")
            
        # Try to find toggle button (should not exist for admin)
        toggle_buttons = admin_row.find_elements(By.CSS_SELECTOR, "[id^='toggle-btn-']")
        self.assertEqual(len(toggle_buttons), 0, "Toggle button should not exist for admin user")

    def test_page_load(self):
        """Test if users page loads correctly"""
        self.driver.get(f"{self.base_url}/users")
        
        # Wait for the table to be visible
        table = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table"))
        )
        
        # Verify page title
        self.assertIn("User Management", self.driver.title)
        
        # Verify table headers
        headers = table.find_elements(By.TAG_NAME, "th")
        expected_headers = ["USERNAME", "EMAIL", "ROLE", "STATUS", "ACTIONS"]
        actual_headers = [header.text for header in headers]
        self.assertEqual(expected_headers, actual_headers)
        
        # Verify add user button exists
        add_button = self.driver.find_element(By.CSS_SELECTOR, "[data-bs-target='#addUserModal']")
        self.assertTrue(add_button.is_displayed())

if __name__ == "__main__":
    unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(
        output='test_reports',
        report_name="user_management_ui_test_report",
        combine_reports=True,
        report_title="User Management UI Test Report"
    ))
