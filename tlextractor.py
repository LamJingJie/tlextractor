from colorama import Fore
from playwright.sync_api import sync_playwright, Page
import json

url = str()
target = []
val = str()

# Tasks
# 1. Extract data(json/svg) from the page its currently at
#    -> Perform data transformation, only saving the necessary data
# 2. Fork tldraw prj and make changes to its layout/template
# 3. Split the json data to image, names, and other data

# Example: https://www.tldraw.com/r/eRZwoL-G5ufBB3KTRaSbW?v=-659,-888,5720,4826&p=HGtpLC0ipiTvgK6awql7m


# playwrite bot
def ActivateBot(url, chosen_frame, page: Page):
    tldraw_menu_list = '.tlui-page-menu__list'
    tldraw_menu_item = '.tlui-page-menu__item'

    try:
        page.goto(url)
        page.wait_for_selector(".tlui-popover")
        page.click(".tlui-button__menu")
        page.wait_for_selector(tldraw_menu_list)
        dropdown_menu = page.query_selector_all(tldraw_menu_item)

        if(not Dropdown_Checker(chosen_frame, dropdown_menu)):
            print(Fore.YELLOW + "Page not found. Exiting program." + Fore.RESET)
            exit()
        
        page.wait_for_load_state('load')

        # Right click on the page and copy as JSON
        page.click(".tl-background", button="right")
        page.click("[data-testid='context-menu-sub-trigger.copy-as']")
        page.click("[data-testid='context-menu.copy-as-json']")
        clipboard_content = page.evaluate("navigator.clipboard.readText()")
        json_content = json.loads(clipboard_content)
        
    except Exception as e:
        print(str(e))                            
        exit()

    ExtractData(chosen_frame, json_content)


# Loop through the dropdown menu and click the target page
def Dropdown_Checker(chosen_frame, menu):
    for option in menu:
            value = option.inner_text().lower()
            if chosen_frame == value:
                option.click()
                return True
    return False


# Extract the necessary data from the JSON
def ExtractData(chosen_frame: str, content: json):
    frame_id = ''

    # Get the frame id: Still Big(O) = N but half the iteration using 2 pointer
    start_pointer = 0
    end_pointer = len(content['shapes']) - 1
    while start_pointer < end_pointer:
        start_shape = content['shapes'][start_pointer]
        end_shape = content['shapes'][end_pointer]

        # Get frame where all the data is stored and check if the frame is the chosen frame 
        if start_shape['type'] == 'frame' and chosen_frame == start_shape['props'].get('name', '').lower() and start_shape['parentId'].startswith('page:'):
            frame_id = content['shapes'][start_pointer]['id']
            break
        elif end_shape['type'] == 'frame' and chosen_frame == end_shape['props'].get('name', '').lower() and end_shape['parentId'].startswith('page:'):
            frame_id = content['shapes'][end_pointer]['id']
            break
        start_pointer += 1
        end_pointer -= 1
    
    if frame_id == '':
        print(Fore.YELLOW + "Frame not found. Ensure that the FRAME name matches exactly the PAGE name." + Fore.RESET)
        exit()

    print(frame_id)






while url == "":
    url = input("Tldraw project url: ")


print(Fore.LIGHTMAGENTA_EX + "\nType 'ALL' to extract all frames. Otherwise, enter the frame(s) you want to extract." + Fore.RESET)
while True:
    val = input(Fore.LIGHTMAGENTA_EX+"\nWhen finished type 'DONE'.\n:: " + Fore.RESET).lower()

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
    print(Fore.YELLOW + "No frames selected. Exiting program." + Fore.RESET)
    exit()


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(permissions=["clipboard-read", "clipboard-write"]) # Add clipboard permissions
    if (target[0] == "all"):
        # Extract all data
        pass
    else:
        # loop and extract each frame
        for frame in target:
            page = context.new_page()
            ActivateBot(url, frame, page)
    context.close()
    browser.close()


    



