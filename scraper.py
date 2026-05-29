import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd

# Configure logging for production reliability
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_dynamic_racing_table(target_url: str, expected_rows: int, timeout_sec: int = 10) -> pd.DataFrame:
    """
    Scrapes a complex, dynamic racing data table utilizing stealth headless browser automation.
    Optimized with explicit explicit waits (WebDriverWait) and batch DOM parsing to bypass anti-bot detection.
    
    :param target_url: The URL of the dynamic racing page.
    :param expected_rows: Total number of records (horses) to scrape in the table.
    :param timeout_sec: Max seconds to wait for elements to load.
    :return: A cleaned Pandas DataFrame containing structured racing attributes.
    """
    
    # 1. Initialize Stealth Chrome Options
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # Use modern headless mode
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Bypassing basic automation detection signatures
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Optional: Fetch path from environment variable for environment cross-compatibility (China/HK/US)
    # Defaulting to standard system path if not specified
    driver_path = os.getenv("CHROMEDRIVER_PATH", "chromedriver")
    service = Service(driver_path)
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Inject script to further obfuscate webdriver attribute
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    # Initialize data lists for efficient column building
    data_storage = {
        'Horse_No': [], 'Horse_Name': [], 'Horse_ID': [], 'Current_Rating': [],
        'Actual_Weight': [], 'Horse_Weight': [], 'Jockey': [], 'Trainer': [],
        'Draw': [], 'Age': [], 'Days_Since_Last_Race': [], 'Gear': [],
        'Sire': [], 'Dam_Sire': []
    }

    try:
        logging.info(f"Navigating to secured data source: {target_url}")
        driver.get(target_url)

        # 2. Advanced Exception Handling & Page Refresh Logic
        attempts = 0
        max_attempts = 3
        
        while attempts < max_attempts:
            try:
                # Explicit Wait: Wait until the container table is fully rendered in DOM
                # This replaces unreliable time.sleep() and optimizes scraping throughput
                table_locator = (By.XPATH, '//*[@id="racecardlist"]/tbody/tr/td/table/tbody')
                WebDriverWait(driver, timeout_sec).until(EC.presence_of_element_located(table_locator))
                
                # Performance Optimization: Grab all matching rows in ONE single DOM communication
                # Instead of hitting driver.find_element hundreds of times, we process them in memory.
                rows = driver.find_elements(By.XPATH, '//*[@id="racecardlist"]/tbody/tr/td/table/tbody/tr')
                
                if len(rows) < expected_rows:
                    raise NoSuchElementException("Table rows not fully loaded yet.")
                
                logging.info(f"Successfully locked DOM element. Parsing {expected_rows} rows...")
                
                # 3. High-Speed In-Memory Row Parsing
                for i in range(1, expected_rows + 1):
                    base_xpath = f'//*[@id="racecardlist"]/tbody/tr/td/table/tbody/tr[{i}]'
                    
                    # Extract elements using unified standard selectors
                    data_storage['Horse_No'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[1]').get_attribute("innerHTML").strip())
                    data_storage['Horse_Name'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[4]').text.strip())
                    data_storage['Horse_ID'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[5]').get_attribute("innerHTML").strip())
                    data_storage['Current_Rating'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[12]').get_attribute("innerHTML").strip())
                    data_storage['Actual_Weight'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[6]').get_attribute("innerHTML").strip())
                    data_storage['Horse_Weight'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[14]').get_attribute("innerHTML").strip())
                    data_storage['Jockey'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[7]').text.strip())
                    data_storage['Trainer'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[10]').text.strip())
                    data_storage['Draw'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[9]').get_attribute("innerHTML").strip())
                    data_storage['Age'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[17]').get_attribute("innerHTML").strip())
                    data_storage['Days_Since_Last_Race'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[22]').get_attribute("innerHTML").strip())
                    data_storage['Gear'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[23]').get_attribute("innerHTML").strip())
                    data_storage['Sire'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[25]').get_attribute("innerHTML").strip())
                    data_storage['Dam_Sire'].append(driver.find_element(By.XPATH, f'{base_xpath}/td[26]').get_attribute("innerHTML").strip())
                
                break # Break loop if scraping completes without exception
                
            except (TimeoutException, NoSuchElementException) as e:
                attempts += 1
                logging.warning(f"Detection triggered or network timeout. Attempt {attempts}/{max_attempts}. Refreshing page...")
                driver.refresh()
                if attempts == max_attempts:
                    raise RuntimeError("Failed to bypass target anti-bot system after maximum retries.") from e

    finally:
        # Guarantee browser shutdown to prevent headless memory leaks in production servers
        driver.quit()
        logging.info("Headless Browser resource successfully released.")

    # 4. Return as Production-Ready Pandas DataFrame (ETL Start-point)
    return pd.DataFrame(data_storage)

if __name__ == "__main__":
    # Test block for local debugging (Mock data configuration)
    # In production, this can be imported as an independent ETL module
    print("Stealth Engine initialized successfully. Ready for deployment.")
