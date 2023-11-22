from selenium import webdriver
from time import sleep
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException


comment_list = []

# 1. Khai báo browser
driver = webdriver.Chrome(service=ChromeService(
    ChromeDriverManager().install()))

# 2. Mở URL của post
driver.get(
    "https://www.foody.vn/ho-chi-minh/sui-cao-hem-191-ha-ton-quyen/binh-luan")
sleep(random.randint(5, 10))

review_count = driver.find_element(
    "xpath", "/html/body/div[2]/div[2]/div[2]/section/div/div/div/div/div[1]/div/div/div[1]/div/div[1]/div/ul/li[1]/a/span")

review_count = int(review_count.text)
# click_count = int(review_count/10)
print(f"Có {review_count} bình luận.")
# get li
for i in range(review_count):
    print(f"Crawl bình luận thứ {i}")
    try:
        if i % 10 == 0:
            showcomment_link = driver.find_element(
                "xpath", "/html/body/div[2]/div[2]/div[2]/section/div/div/div/div/div[1]/div/div/div[1]/div/div[2]/a")
            showcomment_link.click()
            # sleep(random.randint(5, 10))
    except NoSuchElementException:
        print("No Such Element Exception!" + str(i))
    li_elements = driver.find_elements(
        "xpath", f"/html/body/div[2]/div[2]/div[2]/section/div/div/div/div/div[1]/div/div/div[1]/div/ul/li[{i}]/div[2]/div")

    for li in li_elements:
        comment_list.append(li.text)
with open('comments.txt', 'w', encoding='utf-8') as file:
    for comment in comment_list:
        file.write(comment + '\n')

driver.close()

print(comment_list)
