from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# Initialize WebDriver
service = Service("C:/Program Files (x86)/chromedriver.exe")  # Update with your ChromeDriver path
driver = webdriver.Chrome(service=service)
url = "http://kickoff.ai/matches/33"  # Replace with the actual URL
driver.get(url)
print(driver.title)

# Click the "Show more" button 10 times
try:
    for i in range(10):  # Adjust the number of clicks as needed
        show_more_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "more-matches-all"))
        )
        show_more_button.click()
        print(f"Clicked 'Show more' button {i + 1} times.")
        time.sleep(2)  # Pause to allow new matches to load
except Exception as e:
    print("No more 'Show more' button or error clicking:", e)

# Wait for all "prediction prediction-result" sections to load
try:
    all_sections = WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[@class='prediction prediction-result']"))
    )
    print(f"Found {len(all_sections)} 'prediction prediction-result' sections.")
except Exception as e:
    print(f"Error locating 'prediction prediction-result' sections: {e}")
    driver.quit()
    exit()

# Extract match details from all sections and click each match
all_matches = []
match_id = 1  # Start match ID numbering

for section in all_sections:
    try:
        matches = section.find_elements(By.XPATH, ".//a[@href]")
        print(f"Found {len(matches)} matches in the current section.")

        for match in matches:
            try:
                # Extract basic match details
                home_team = match.find_element(By.XPATH, ".//div[@class='team-home']//span[@class='team-name']").text
                away_team = match.find_element(By.XPATH, ".//div[@class='team-away']//span[@class='team-name']").text
                result = match.find_element(By.XPATH, ".//div[@class='result']").text if "result" in match.get_attribute("outerHTML") else "N/A"
                match_time = match.find_element(By.XPATH, ".//div[@class='match-time-list']").text

                # Extract goals scored by each team if result is available
                if result != "N/A":
                    home_goals, away_goals = map(int, result.split(":"))
                else:
                    home_goals, away_goals = None, None

                # Click on the match to extract percentages
                match.click()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "prediction-percentages"))
                )

                # Extract percentages and convert to decimals
                victory_percentage = float(driver.find_element(By.CLASS_NAME, "prediction-win-home").text.strip('%')) / 100
                draw_percentage = float(driver.find_element(By.CLASS_NAME, "prediction-draw").text.strip('%')) / 100
                loss_percentage = float(driver.find_element(By.CLASS_NAME, "prediction-win-away").text.strip('%')) / 100

                # Determine binary outcomes
                if home_goals is not None and away_goals is not None:
                    home_team_wins = 1 if home_goals > away_goals else 0
                    match_ties = 1 if home_goals == away_goals else 0
                else:
                    home_team_wins = None
                    match_ties = None
                if home_team_wins ==0 and match_ties==0:
                    home_team_looses=1
                else:
                    home_team_looses=0

                # Save data with Match ID
                all_matches.append({
                    "Match ID": match_id,
                    "Home Team": home_team,
                    "Away Team": away_team,
                    "Time/Date": match_time,
                    "Home Goals": home_goals,
                    "Away Goals": away_goals,
                    "Victory Percentage": victory_percentage,
                    "Draw Percentage": draw_percentage,
                    "Loss Percentage": loss_percentage,
                    "Home Team Wins": home_team_wins,
                    
                    "Match Ties": match_ties,
                     "Home Team Looses": home_team_looses,
                })

                print(f"Match ID: {match_id} | {home_team} vs {away_team} | Time: {match_time} | "
                      f"Goals: {home_goals}-{away_goals} | Victory: {victory_percentage} | "
                      f"Draw: {draw_percentage} | Loss: {loss_percentage} | "
                      f"Home Wins: {home_team_wins} | Match Ties: {match_ties}")

                # Increment Match ID
                match_id += 1

                # Go back to the previous page
                driver.back()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@class='prediction prediction-result']"))
                )

            except Exception as e:
                print(f"Error processing match: {e}")
                driver.back()
                continue

    except Exception as e:
        print(f"Error processing section: {e}")
        continue

# Close WebDriver
driver.quit()

# Save results to an Excel file
df = pd.DataFrame(all_matches)
output_file = "Past_Results_matches.xlsx"
df.to_excel(output_file, index=False)

print(f"All matches data saved to {output_file}")
print(df)
