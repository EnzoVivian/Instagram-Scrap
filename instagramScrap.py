from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import random
import json
import re

load_dotenv()

USERNAME = os.getenv('USUARIO')
PASSWORD = os.getenv('PASSWORD')

def navigator_initializer():
    return webdriver.Firefox()

def instagram_login(browser):
    browser.get("https://www.instagram.com/")
    try:
        time.sleep(1)
        username = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
        username.send_keys(USERNAME)

        time.sleep(2)
        password = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
        password.send_keys(PASSWORD)

        time.sleep(1)
        login = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        login.click()
    except:
        print("Login error.")

def ignore_save_login(browser):
    try:
        time.sleep(3)   
        not_now = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @tabindex='0' and contains(text(), 'Agora não')]")))
        not_now.click()
    except:
        print("Error clicking in not now button.")

def search_user(browser, user):
    searchbutton = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[@role='link']//span[contains(text(), 'Pesquisa')]")))
    searchbutton.click()   
    searchbox = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Pesquisar']")))
    searchbox.clear()
    searchbox.send_keys(user)
    time.sleep(random.randint(1, 3))
    try:
        user_page = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//a[@href='/{user}/']"))
        )
        user_page.click()
    except:
        print(f"User '{user}' not found.")
        return False
    return True

def collect_biography(browser):
    try:
        try:
            WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@role='button' and contains(., 'mais')]//span[@dir='auto']"))).click()
        except:
            print("Error clicking in more button.")
            pass
        return WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='button']//span[@dir='auto']"))
        ).text
    except:
        print("Error collecting biography.")
        return ""
        
def collect_links(browser):
    link_urls = []
    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Ícone de link']"))
        ).click()
        links = WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[@rel='me nofollow noopener noreferrer']")))
        for link in links:
            href = link.get_attribute("href")
            if href:
                link_urls.append(href)
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Fechar']"))
        ).click()
    except:
        try:
            links = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@rel='me nofollow noopener noreferrer']"))
            ).text
        except:
            print("Error collecting links.")
            pass
    return link_urls

def collect_posts(browser):
    posts, posts_src = [], []
    altura_atual = browser.execute_script("return document.body.scrollHeight")
    count = 0
    while True:
        try:
            posts_elements = WebDriverWait(browser, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@style, 'display: flex; flex-direction: column;')]//img[@alt and @crossorigin and @style and @src]"))
            )
            for post in posts_elements:
                src = post.get_attribute("src")
                description = post.get_attribute("alt")
                if description and src not in posts_src:
                    posts_src.append(src)
                    date = collect_post_date(description)
                    if description and date:
                        posts.append({"description": str(description), "date": str(date)})
                        count += 1
                        print(f"Post {count}: {description} | Date: {date}")
                    else:
                        print("No new posts.")
        except:
            print("Error collecting posts.")
        
        browser.execute_script("window.scrollBy(0, document.body.scrollHeight)")
        time.sleep(random.randint(2, 3))
        altura_nova = browser.execute_script("return document.body.scrollHeight")
        if altura_nova == altura_atual:
            break
        altura_atual = altura_nova
    return posts

def collect_post_date(description):
    date_pattern = re.search(r'on (\w+ \d{1,2}, \d{4})', description)
    return date_pattern.group(1) if date_pattern else "Unknown"

def save_profile_info_txt(user, biography, link_urls, posts, output_txt_file):
    with open(output_txt_file, "a", encoding="utf-8") as file:
        file.write(f"Profile:\n{user}\nBiography:\n{biography}\nLinks: \n{';\n'.join(link_urls)}\nPosts:\n")
        for post in posts:
            file.write(f"- Date: {post['date']} | Description: {post['description']}\n")
        file.write("\n")

def save_profile_info_json(profiles, output_json_file):
    with open(output_json_file, "r", encoding="utf-8") as json_file:
        existing_data = json.load(json_file)
    existing_data.append(profiles)

    with open(output_json_file, "w", encoding="utf-8") as json_file:
        json.dump(existing_data, json_file, indent=4, ensure_ascii=False)

def main():
    browser = navigator_initializer()
    instagram_login(browser)
    ignore_save_login(browser)
    output_txt_file = "results/instagram_profiles.txt"
    output_json_file = "results/instagram_profiles.json"
    profiles = []
    while True:
        user = input("Enter the username or type 'exit' to quit: ")
        if user.lower() == "exit":
            break
        start_time = time.time()
        
        if search_user(browser, user):
            biography = collect_biography(browser)
            link_urls = collect_links(browser)
            posts = collect_posts(browser)
            profile_info = {"Username": user, "Biography": biography, "Links": link_urls, "Posts": posts}
            profiles.append(profile_info)
            save_profile_info_json(profiles, output_json_file)
            save_profile_info_txt(user, biography, link_urls, posts, output_txt_file)
            print(f"The profile information of {user} has been saved.")
            print(f"Execution time: {time.time() - start_time:.2f} seconds.")
    browser.quit()

if __name__ == "__main__":
    main()