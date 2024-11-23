import unittest
import HtmlTestRunner
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test classes
from tests.test_menu_navigation import TestMenuNavigation
from tests.test_users_ui import TestUserManagementUI
from tests.test_form_inputs import TestFormInputs

def create_test_suite():
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMenuNavigation))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestUserManagementUI))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFormInputs))
    
    return suite

if __name__ == '__main__':
    # Create test suite
    suite = create_test_suite()
    
    # Configure HTML test runner
    runner = HtmlTestRunner.HTMLTestRunner(
        output='tests/test_reports',
        report_name="db_monitor_ui_test_report",
        combine_reports=True,
        report_title="Database Monitor UI Test Report",
        add_timestamp=False,
        template=os.path.join(os.path.dirname(__file__), 'report_template.html')
    )
    
    # Run the test suite
    runner.run(suite)
