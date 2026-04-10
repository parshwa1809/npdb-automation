import os
import glob
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

NPDB_PAGE_URL = "https://www.npdb.hrsa.gov/resources/publicData.jsp"

NPDB_CONTACT = {
    "name": os.environ["NPDB_NAME"],
    "title": os.environ.get("NPDB_TITLE", "Independent Researcher"),
    "city": os.environ["NPDB_CITY"],
    "state": os.environ["NPDB_STATE"],
    "email": os.environ["NPDB_EMAIL"],
    "receive_updates": os.environ.get("NPDB_RECEIVE_UPDATES", "true").lower() == "true",
}

DOWNLOAD_DIR = os.path.abspath("downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def try_type_by_label_text(driver, label_text_candidates, value):
    for txt in label_text_candidates:
        try:
            label = driver.find_element(
                By.XPATH,
                f"//label[contains(translate(normalize-space(.), "
                f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
                f"'{txt.lower()}')]"
            )
            for_attr = label.get_attribute("for")
            if for_attr:
                inp = driver.find_element(By.ID, for_attr)
                inp.clear()
                inp.send_keys(value)
                return True

            inp = label.find_element(By.XPATH, ".//following::input[1]")
            inp.clear()
            inp.send_keys(value)
            return True
        except:
            pass
    return False

def latest_download_file(download_dir, wait_seconds=180):
    end = time.time() + wait_seconds
    while time.time() < end:
        files = [
            f for f in glob.glob(os.path.join(download_dir, "*"))
            if not f.endswith(".crdownload")
        ]
        if files:
            latest = max(files, key=os.path.getmtime)
            time.sleep(2)
            return latest
        time.sleep(2)
    raise RuntimeError("No downloaded file found")

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(NPDB_PAGE_URL)

        try_type_by_label_text(driver, ["name"], NPDB_CONTACT["name"])
        try_type_by_label_text(driver, ["title"], NPDB_CONTACT["title"])
        try_type_by_label_text(driver, ["city"], NPDB_CONTACT["city"])
        try_type_by_label_text(driver, ["e-mail address", "email address", "email"], NPDB_CONTACT["email"])

        for xp in [
            "//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'state')]/following::select[1]",
            "//select[contains(@name,'state') or contains(@id,'state')]"
        ]:
            try:
                sel = Select(driver.find_element(By.XPATH, xp))
                try:
                    sel.select_by_visible_text(NPDB_CONTACT["state"])
                except:
                    sel.select_by_value(NPDB_CONTACT["state"])
                break
            except:
                pass

        for xp in [
            "//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'record type')]/following::select[1]",
            "//select[contains(@name,'record') or contains(@id,'record')]"
        ]:
            try:
                Select(driver.find_element(By.XPATH, xp)).select_by_visible_text("All")
                break
            except:
                pass

        for xp in [
            "//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'profession type')]/following::select[1]",
            "//select[contains(@name,'profession') or contains(@id,'profession')]"
        ]:
            try:
                Select(driver.find_element(By.XPATH, xp)).select_by_visible_text("All")
                break
            except:
                pass

        file_format_set = False
        for xp in [
            "//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'file format')]/following::select[1]",
            "//select[contains(@name,'format') or contains(@id,'format')]"
        ]:
            try:
                sel = Select(driver.find_element(By.XPATH, xp))
                for opt in ["CSV", "CSV Version"]:
                    try:
                        sel.select_by_visible_text(opt)
                        file_format_set = True
                        break
                    except:
                        pass
                if file_format_set:
                    break
            except:
                pass

        if not file_format_set:
            raise RuntimeError("Could not set NPDB file format to CSV")

        for xp in [
            "//input[@type='checkbox' and (contains(@name,'agree') or contains(@id,'agree'))]",
            "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i have read and agree to the data use agreement')]"
        ]:
            try:
                driver.find_element(By.XPATH, xp).click()
                break
            except:
                pass

        clicked_continue = False
        for xp in [
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
            "//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
            "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]"
        ]:
            try:
                driver.find_element(By.XPATH, xp).click()
                clicked_continue = True
                break
            except:
                pass

        if not clicked_continue:
            raise RuntimeError("Could not find NPDB Continue/submit button")

        file_path = latest_download_file(DOWNLOAD_DIR, wait_seconds=180)
        print(f"Downloaded file: {file_path}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
