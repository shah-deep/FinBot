import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time


class TestChatApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up the browser driver (e.g., ChromeDriver)
        # Ensure ChromeDriver is in PATH or provide the executable path
        cls.driver = webdriver.Chrome()  
        cls.base_url = "http://127.0.0.1:8050/"

    @classmethod
    def tearDownClass(cls):
        # Close the browser after all tests
        cls.driver.quit()

    def test_redirect_on_ticker_input(self):
        driver = self.driver
        driver.get(self.base_url)

        # Find the input box and enter the company ticker
        ticker_input = driver.find_element(By.TAG_NAME, "input") 
        ticker_input.send_keys("NVDA")
        ticker_input.send_keys(Keys.RETURN)

        time.sleep(4) 

        # Assert the URL change
        self.assertIn("/c/?t=NVDA", driver.current_url)

    def test_chat_response(self):
        driver = self.driver
        driver.get(f"{self.base_url}c/?t=NVDA")

        # Find the chat input box and enter a query
        chat_input = driver.find_element(By.ID, "user-input") 
        chat_input.send_keys("Get ROE")
        chat_input.send_keys(Keys.RETURN)

        time.sleep(5)  

        chat_response = driver.find_element(By.CLASS_NAME, "card-body")  # Replace with actual response element class
        self.assertTrue("ROE" in chat_response.text)


if __name__ == "__main__":
    # Get Return on Equity (ROE), Return on Assets (ROA), Net Profit Margin, Gross Margin, Debt to Equity, and Interest Coverage.
    # Show a comparision of closing prices, moving average for window 15, short moving average, long moving average, and exponential moving average for span 5.
    unittest.main()
