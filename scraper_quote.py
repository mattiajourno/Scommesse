from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
import time
import platform
import os

class OddScraper:
    
    def __init__(self, data_path="data", file_name="oddsportal.csv"):
        self.data_path = data_path
        self.file_name = file_name
        
    def scrape(self, num_pages=10):
        
        match platform.system():
            case "Linux":
                options = webdriver.FirefoxOptions()
                options.add_argument("-headless")
                driver = webdriver.Firefox(options=options)
            case "Windows":
                service = Service("C:/Program Files (x86)/chromedriver.exe")
                driver = webdriver.Chrome(service=service)
            case _:
                raise NotImplementedError("Not implemented in this OS")
        
        # Open the target URL
        url = "https://www.oddsportal.com/it/search/results/:zVqqL0ma/page/1/"  # Replace with the actual URL
        driver.get(url)
        print(driver.title)
        
        # Initialize list for storing results
        all_data = []
        
        Accuracy = 0
        n = 0
        
        # Process up to 10 pages
        for page in range(1, num_pages):  # Loop from page 1 to page 10
            print(f"Processing page {page}...")
            try:
                # Wait for the page to load
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "eventRow"))
                )
        
                # Find all game rows
                game_rows = driver.find_elements(By.CLASS_NAME, "eventRow")
        
                for i, game in enumerate(game_rows, start=1):
                    try:
                        # Extract odds for the game
                        odds_elements = game.find_elements(By.CSS_SELECTOR, 'p.height-content')
                        odds = [odd.text for odd in odds_elements]
                        n += 1
        
                        # Initialize result vector as all zeros
                        result_vector = [0, 0, 0]
        
                        # Check each odds element for the `gradient-green hover` class
                        for idx, odd_element in enumerate(odds_elements):
                            class_attribute = odd_element.get_attribute("class")
                            if "gradient-green hover" in class_attribute:  # Check if the event occurred
                                result_vector[idx] = 1
        
                        # Ensure there are three odds
                        if len(odds) == 3:
                            match_data = {
                                "Page": page,
                                "Match ID": i,
                                "Odds (1)": float(odds[0]),
                                "Odds (X)": float(odds[1]),
                                "Odds (2)": float(odds[2]),
                                "P (1)": 0.95 / float(odds[0]),
                                "P (X)": 0.95 / float(odds[1]),
                                "P (2)": 0.95 / float(odds[2]),
                                "Victory": result_vector[0],
                                "Tie": result_vector[1],
                                "Loss": result_vector[2],
                            }
                            P = [0.95 / float(odds[0]), 0.95 / float(odds[1]), 0.95 / float(odds[2])]
                            Accuracy += np.dot(P, result_vector)
        
                            # Append match data to the single list
                            all_data.append(match_data)
        
                            print(
                                f"Page {page} | Match ID: {i} | Odds: {odds} | Result Vector: {result_vector}"
                            )
                        else:
                            print(f"Page {page} | Match ID: {i} - Could not extract all three odds.")
        
                    except Exception as e:
                        print(f"Error processing game {i} on page {page}: {e}")
                        continue
        
                # Click the next page button
                if page < 10:  # Avoid clicking next on the last page
                    try:
                        next_button = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, f"//a[@data-number='{page + 1}']"))
                        )
        
                        # Scroll to the next button to ensure it's in the viewport
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                        time.sleep(1)  # Allow scrolling time
        
                        # Use JavaScript to click the button
                        driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(3)  # Allow time for the next page to load
                    except Exception as e:
                        print(f"Error clicking next button for page {page}: {e}")
                        break
        
            except Exception as e:
                print(f"Error processing page {page}: {e}")
                break
        
        # Calculate accuracy
        Accuracy /= n
        print(f"Accuracy: {Accuracy}")
        
        # Close WebDriver
        driver.quit()
        
        output_file = os.path.join(".", self.data_path, self.file_name)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        pd.DataFrame(all_data).to_csv(output_file, index=False)
        
        print(f"All matches data saved to {output_file}")
