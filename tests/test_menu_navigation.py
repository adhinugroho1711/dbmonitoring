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

class TestMenuNavigation(unittest.TestCase):
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

    def test_dashboard_navigation(self):
        """Test navigation to dashboard and verify content"""
        # Navigate to dashboard
        self.driver.find_element(By.LINK_TEXT, "Dashboard").click()
        
        # Verify URL
        self.assertEqual(self.driver.current_url, f"{self.base_url}/")
        
        # Verify dashboard elements
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "card").is_displayed())

    def test_database_servers_navigation(self):
        """Test navigation to database servers page and verify content"""
        # Navigate to database servers
        self.driver.find_element(By.LINK_TEXT, "Database Servers").click()
        
        # Verify URL
        self.assertEqual(self.driver.current_url, f"{self.base_url}/database_servers")
        
        # Verify page elements
        add_server_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-bs-target='#addServerModal']")
        self.assertTrue(add_server_btn.is_displayed())
        
        # Verify table headers
        headers = self.driver.find_elements(By.TAG_NAME, "th")
        expected_headers = ["NAME", "TYPE", "HOST", "PORT", "USERNAME", "STATUS", "LAST CHECK", "ACTIONS"]
        actual_headers = [header.text for header in headers]
        self.assertEqual(expected_headers, actual_headers)

    def test_users_navigation(self):
        """Test navigation to users page and verify content"""
        # Navigate to users page
        self.driver.find_element(By.LINK_TEXT, "Users").click()
        
        # Verify URL
        self.assertEqual(self.driver.current_url, f"{self.base_url}/users")
        
        # Verify page elements
        add_user_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-bs-target='#addUserModal']")
        self.assertTrue(add_user_btn.is_displayed())
        
        # Verify table headers
        headers = self.driver.find_elements(By.TAG_NAME, "th")
        expected_headers = ["USERNAME", "EMAIL", "ROLE", "STATUS", "ACTIONS"]
        actual_headers = [header.text for header in headers]
        self.assertEqual(expected_headers, actual_headers)

    def test_activity_logs_navigation(self):
        """Test navigation to activity logs page and verify content"""
        # Navigate to activity logs
        self.driver.find_element(By.LINK_TEXT, "Activity Logs").click()
        
        # Verify URL
        self.assertEqual(self.driver.current_url, f"{self.base_url}/activity_logs")
        
        # Verify table headers
        headers = self.driver.find_elements(By.TAG_NAME, "th")
        expected_headers = ["TIME", "USER", "IP ADDRESS", "ACTION"]
        actual_headers = [header.text for header in headers]
        self.assertEqual(expected_headers, actual_headers)

    def test_query_history_navigation(self):
        """Test navigation to query history page and verify content"""
        # Navigate to query history
        self.driver.find_element(By.LINK_TEXT, "Query History").click()
        
        # Verify URL
        self.assertEqual(self.driver.current_url, f"{self.base_url}/query_history")
        
        # Verify table headers
        headers = self.driver.find_elements(By.TAG_NAME, "th")
        expected_headers = ["SERVER", "DATABASE", "USERNAME", "QUERY", "STATUS", "START TIME", "END TIME", "EXECUTION TIME (S)"]
        actual_headers = [header.text for header in headers]
        self.assertEqual(expected_headers, actual_headers)

    def test_logout_functionality(self):
        """Test logout functionality"""
        # Click logout
        self.driver.find_element(By.LINK_TEXT, "Logout").click()
        
        # Verify redirect to login page
        self.assertTrue("/login" in self.driver.current_url)
        
        # Verify login form is present
        login_form = self.driver.find_element(By.TAG_NAME, "form")
        self.assertTrue(login_form.is_displayed())

    def test_navbar_user_display(self):
        """Test that username is displayed in navbar"""
        # Find username element in navbar
        username_elements = self.driver.find_elements(By.CLASS_NAME, "nav-link")
        username_element = None
        for element in username_elements:
            if element.text == self.admin_username:
                username_element = element
                break
        
        # Verify admin username is displayed
        self.assertIsNotNone(username_element, "Username not found in navbar")
        self.assertEqual(username_element.text, self.admin_username)

if __name__ == "__main__":
    unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(
        output='test_reports',
        report_name="menu_navigation_test_report",
        combine_reports=True,
        report_title="Menu Navigation Test Report"
    ))
