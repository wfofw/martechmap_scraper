import sys
import subprocess
import os

def install_requirements():
    req_file = "requirements.txt"
    if os.path.exists(req_file):
        print("📦 Installing dependencies from requirements.txt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
    else:
        print("❌ File requirements.txt not found!")

install_requirements()

import random
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
from dotenv import load_dotenv

import pandas as pd

load_dotenv(dotenv_path="config.env")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def wait_for_element(driver, by, selector, timeout=25):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )

driver = webdriver.Chrome()
driver.set_window_size(1400, 900)
print('chrome inizialized..')
ActionChains(driver).key_down(Keys.CONTROL).send_keys('r').key_up(Keys.CONTROL).perform()
driver.get('https://martechmap.com/login/')
ActionChains(driver).key_down(Keys.CONTROL).send_keys('r').key_up(Keys.CONTROL).perform()
time.sleep(random.uniform(1.5, 2))
print('martechmap.com openned..')

#Input data
email_input = wait_for_element(driver, By.XPATH, '//input[@type="email"]').send_keys(EMAIL)
password_input = wait_for_element(driver, By.XPATH, '//input[@type="password"]')
password_input.send_keys(PASSWORD)
time.sleep(random.uniform(1.1, 1.5))
password_input.send_keys(Keys.ENTER)
time.sleep(random.uniform(1.1, 1.5))
password_input.send_keys(Keys.ENTER)

#Loading https://martechmap.com/int_supergraphic
time.sleep(2.5)
iframe = wait_for_element(driver, By.TAG_NAME, "iframe")
driver.switch_to.frame(iframe)
time.sleep(2.5)

def safe_wait_for_element(driver, by, selector, timeout=10, retries=3):
    from selenium.common.exceptions import TimeoutException
    for i in range(retries):
        try:
            return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
        except TimeoutException:
            print(f"⏳ Retry {i+1}/{retries} — still waiting for {selector}")
            time.sleep(1)
    raise TimeoutException(f"❌ Could not find element: {selector}")


landscape = safe_wait_for_element(driver, By.ID, "landscape")
columns = landscape.find_elements(By.XPATH, './div[starts-with(@class, "column")]')
subcats = landscape.find_elements(By.XPATH, './/div[contains(@class, "subcat")]')

vendors_data = []

all_subcats = driver.find_elements(By.XPATH, '//div[contains(@class, "subcat")]')
total = len(all_subcats)
print(f"🔎 Total vendors: {total}")

def hover_and_extract_tooltip(driver, img, retries=3):
    from selenium.common.exceptions import TimeoutException

    for attempt in range(retries):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
            time.sleep(0.5)
            actions = ActionChains(driver)
            actions.move_to_element(img).perform()

            tooltip = WebDriverWait(driver, 3).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "tooltiptext"))
            )
            return tooltip.text.strip()
        except TimeoutException:
            time.sleep(0.3 + attempt * 0.2)
            continue
        except Exception as e:
            print(f"❌ Hover error: {e}")
            return "N/A"
    return "N/A"

for i in range(total):
    try:
        subcat = driver.find_elements(By.XPATH, '//div[contains(@class, "subcat")]')[i]
        
        try:
            title = subcat.find_element(By.TAG_NAME, 'p').text.strip()
        except:
            title = "N/A"

        vendors_blocks = subcat.find_elements(By.CLASS_NAME, 'vendors_in_subcat')
        if not vendors_blocks:
            # print(f"[{i+1}/{total}] ⚠️ naah vendors")
            continue

        for block in vendors_blocks:
            img_tags = block.find_elements(By.TAG_NAME, 'img')
            def simulate_hover_with_js(driver, element):
                driver.execute_script("""
                    var evObj = document.createEvent('MouseEvents');
                    evObj.initEvent('mouseover', true, false);
                    arguments[0].dispatchEvent(evObj);
                """, element)
            for img in img_tags:
                try:
                    alt_text = img.get_attribute('alt').strip()
                    
                    # 👇 наведение через JS
                    simulate_hover_with_js(driver, img)
                    time.sleep(0.01)

                    tooltip = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "tooltiptext"))
                    )
                    tooltip_text = tooltip.text.strip()

                    def extract(line, key):
                        for l in tooltip_text.splitlines():
                            if key in l:
                                return l.replace(key, "").strip()
                        return ""

                    item = {
                        "subcategory": title,
                        "company": alt_text,
                        "website": extract(tooltip_text, "Site:"),
                        "social": extract(tooltip_text, "Twitter:"),
                        "revenue": extract(tooltip_text, "Revenue:"),
                        "employees": extract(tooltip_text, "Employees:"),
                        "year": extract(tooltip_text, "Year:"),
                        "reviews": extract(tooltip_text, "Reviews:"),
                        "rating": extract(tooltip_text, "Rating:"),
                        "source": extract(tooltip_text, "CabinetM"),
                    }
                    vendors_data.append(item)
                    print(item)

                except Exception as e:
                    print("❌ JS tooltip error:", e)
                    continue


    except Exception as e:
        print(f"[{i+1}/{total}] ❌ error subcat:", e)
        continue
    
    df = pd.DataFrame(vendors_data)
    df.to_csv("vendors.csv", index=False, encoding="utf-8", sep=';')
    driver.quit()