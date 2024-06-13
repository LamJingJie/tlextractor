from colorama import Fore
import re
from playwright.sync_api import sync_playwright, Page
import time

url = str()
target = []
val = str()

# Tasks
# 1. Extract data(json/svg) from the page its currently at
#    -> Perform data transformation, only saving the necessary data

# Example: https://www.tldraw.com/r/eRZwoL-G5ufBB3KTRaSbW?v=-659,-888,5720,4826&p=HGtpLC0ipiTvgK6awql7m

# Extract data from the url
def ExtractData(url, frame, page: Page):
    tldraw_menu_list = '.tlui-page-menu__list'
    tldraw_menu_item = '.tlui-page-menu__item'

    try:
        page.goto(url)
        page.wait_for_selector(".tlui-popover")
        page.click(".tlui-button__menu")
        page.wait_for_selector(tldraw_menu_list)
        dropdown_menu = page.query_selector_all(tldraw_menu_item)

        # Loop through the dropdown menu and click the target page
        for option in dropdown_menu:
            value = option.inner_text().lower()
            print("loop:",value)
            if frame == value:
                option.click()
                break
        
        page.wait_for_load_state('load')
        time.sleep(5)
        page.screenshot(path="jingjie.png")


    except Exception as e:
        print(str(e))
        exit()


    


while url == "":
    url = input("Tldraw project url: ")


print("\nType 'ALL' to extract all frames. Otherwise, enter the frame(s) you want to extract.")
while True:
    val = input("When finished type 'DONE'.\n::").lower()

    # Check if the user wants to extract all frames
    if (len(target) == 0 and val == "all"):
        target.append(val)
        break

    # Check if the user wants to stop entering frames
    if (val == "done"):
        break

    # Check if the user entered a value
    if (val != ""):
        target.append(val)



if (len(target) == 0):
    print(Fore.RED + "No frames selected. Exiting program.")
    exit()


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    if (target[0] == "all"):
        # Extract all data
        pass
    else:
        # loop and extract each frame
        for frame in target:
            page = browser.new_page()
            ExtractData(url, frame, page)
    browser.close()


    



