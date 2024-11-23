import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class TestFormInputs(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)
        self.base_url = "http://127.0.0.1:5000"
        self.driver.get(f"{self.base_url}/login")
        
        # Login as admin
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        username.send_keys("admin")
        password.send_keys("change-this-password")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for dashboard to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "card-title"))
        )

    def tearDown(self):
        """Clean up after each test"""
        if self.driver:
            self.driver.quit()

    def test_add_user_form(self):
        """Test the Add User form functionality"""
        # Navigate to Users page
        self.driver.find_element(By.LINK_TEXT, "Users").click()
        
        # Click Add User button
        add_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-bs-target='#addUserModal']"))
        )
        add_button.click()
        
        # Wait for modal to appear and be visible
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "addUserModal"))
        )
        
        # Test form validation - Empty submission
        save_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[onclick='saveUser()']"))
        )
        save_button.click()
        
        # Check for required field validation
        username_input = self.driver.find_element(By.ID, "username")
        self.assertEqual(username_input.get_attribute("required"), "true",
                        "Username field is not marked as required")
        
        # Test form validation - Invalid email
        username_input.send_keys("testuser")
        email_input = self.driver.find_element(By.ID, "email")
        email_input.send_keys("invalid-email")
        password_input = self.driver.find_element(By.ID, "password")
        password_input.send_keys("testpass123")
        
        save_button.click()
        self.assertEqual(email_input.get_attribute("type"), "email",
                        "Email field is not using email type validation")
        
        # Test successful form submission
        email_input.clear()
        email_input.send_keys("testuser@example.com")
        save_button.click()
        
        # Wait for modal to close
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "addUserModal"))
        )
        
        # Verify user appears in table
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        user_rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        found_user = False
        for row in user_rows:
            if "testuser" in row.text:
                found_user = True
                break
        self.assertTrue(found_user, "New user not found in table")

    def test_add_database_server_form(self):
        """Test the Add Database Server form functionality"""
        # Navigate to Database Servers page
        self.driver.find_element(By.LINK_TEXT, "Database Servers").click()
        
        # Click Add Server button
        add_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-bs-target='#addServerModal']"))
        )
        add_button.click()
        
        # Wait for modal to appear and be visible
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "addServerModal"))
        )
        
        # Test form validation - Empty submission
        submit_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[onclick='submitServer()']"))
        )
        submit_button.click()
        
        # Check for required field validation
        name_input = self.driver.find_element(By.ID, "name")
        self.assertEqual(name_input.get_attribute("required"), "true",
                        "Server name field is not marked as required")
        
        # Test form validation - Invalid port
        name_input.send_keys("Test DB")
        host_input = self.driver.find_element(By.ID, "host")
        host_input.send_keys("localhost")
        port_input = self.driver.find_element(By.ID, "port")
        port_input.send_keys("invalid_port")
        username_input = self.driver.find_element(By.ID, "username")
        username_input.send_keys("dbuser")
        password_input = self.driver.find_element(By.ID, "password")
        password_input.send_keys("dbpass123")
        
        submit_button.click()
        self.assertEqual(port_input.get_attribute("type"), "number",
                        "Port field is not using number type validation")
        
        # Test successful form submission
        port_input.clear()
        port_input.send_keys("5432")
        submit_button.click()
        
        # Wait for error alert or modal to close
        try:
            error_alert = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.ID, "errorAlert"))
            )
            if "d-none" not in error_alert.get_attribute("class"):
                self.fail(f"Server add failed: {error_alert.text}")
        except TimeoutException:
            pass
        
        # Verify server appears in table
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        server_rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        found_server = False
        for row in server_rows:
            if "Test DB" in row.text:
                found_server = True
                break
        self.assertTrue(found_server, "New server not found in table")

    def test_login_form(self):
        """Test the login form functionality"""
        # Logout first
        self.driver.find_element(By.LINK_TEXT, "Logout").click()
        
        # Wait for login page
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card-title"))
        )
        
        # Test empty form submission
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Check for required field validation
        username_input = self.driver.find_element(By.ID, "username")
        self.assertEqual(username_input.get_attribute("required"), "true",
                        "Username field is not marked as required")
        
        # Test invalid credentials
        username_input.send_keys("wronguser")
        password_input = self.driver.find_element(By.ID, "password")
        password_input.send_keys("wrongpass")
        submit_button.click()
        
        # Verify we're still on login page
        time.sleep(1)  # Wait for potential redirect
        self.assertIn("login", self.driver.current_url.lower())
        
        # Test successful login
        username_input.clear()
        password_input.clear()
        username_input.send_keys("admin")
        password_input.send_keys("change-this-password")
        submit_button.click()
        
        # Verify successful login
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card-title"))
        )
        self.assertIn("dashboard", self.driver.current_url.lower())

if __name__ == '__main__':
    unittest.main()
                EC.presence_of_element_located((By.CLASS_NAME, "card-title"))
            )
            # Finally verify we're on dashboard
            self.assertTrue(
                "/dashboard" in self.driver.current_url or 
                self.driver.current_url.endswith("/"),
                "Not redirected to dashboard"
            )
        except TimeoutException as e:
            self.fail(f"Login redirect failed: {str(e)}")

if __name__ == '__main__':
    unittest.main()
