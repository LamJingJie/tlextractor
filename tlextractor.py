from colorama import Fore
from playwright.sync_api import sync_playwright, Page, BrowserContext
import json
import base64
import requests
import threading
import sys
import time

# Data Structure
'''[
    {
        "name": "benchmark 01",
        "date": "DUE 26 MAY (SUNDAY) 2359",
        "description": "First iteration of site in blender/rhino",
        "data": [
            {
                "Jia Wei": 
                    {
                        "image": [
                                    "base64_img", "base64_img"
                                 ]
                    },
            }
        ]
    }
]'''

# Example: https://www.tldraw.com/r/fOZmgi9MQzQc-rrXnpAz6?v=-167,-196,5343,2630&p=HGtpLC0ipiTvgK6awql7m

#Video
'''
https://github-production-user-asset-6210df.s3.amazonaws.com/58838335/340716156-68d26e9a-b312-4af8-9200-c902aa7527f3.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20240618%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240618T143126Z&X-Amz-Expires=300&X-Amz-Signature=38cc577f04cab4a33903b9ba850aceb69ce931e4fda028dd33d43ce8678bd1cb&X-Amz-SignedHeaders=host&actor_id=58838335&key_id=0&repo_id=813742945
'''

# -----------------Functions-----------------#

# Process pages chosen by the user
def process_pages(url, targets, context: BrowserContext):
    prj_title = ''
    all_page_data = []

    # Get project title
    page = context.new_page()
    page.goto(url)
    page.wait_for_selector(".tlui-popover")
    page.click(".tlui-button__menu")
    prj_title = page.query_selector(".tlui-top-zone__container").inner_text().strip().replace('\u00a0', ' ')
    page.close()
    
    # Loop through each frame and extract the data
    for frame in targets:
        stop_loading = threading.Event()
        loading_thread = threading.Thread(target=loading_screen, args=(frame, stop_loading))
        loading_thread.start() # Start the loading screen

        page = context.new_page()
        try:
            page_data = ActivateBot(url, frame, page)
            all_page_data.append(page_data)
        except Exception as e:
            # This is added to ensure that the loading screen stops and the thread is joined before the program exits
            page.close()
            stop_loading.set() # Stop the loading screen
            loading_thread.join() # Wait for the loading screen to finish
            raise Exception("Error 00:",str(e))

        page.close()
        stop_loading.set() # Stop the loading screen
        loading_thread.join() # Wait for the loading screen to finish

    website_data = {
        "project title": prj_title,
        "data": all_page_data
    }

    return website_data, prj_title

# playwrite bot for each page
def ActivateBot(url, chosen_frame, page: Page):
    tldraw_menu_list = '.tlui-page-menu__list'
    tldraw_menu_item = '.tlui-page-menu__item'

    try:
        page.goto(url)
        page.wait_for_selector(".tlui-popover")
        page.click(".tlui-button__menu")

        page.wait_for_selector(tldraw_menu_list)
        dropdown_menu = page.query_selector_all(tldraw_menu_item)

        if (not Dropdown_Checker(chosen_frame, dropdown_menu)):
            raise Exception("Page not found. Exiting program.")

        page.wait_for_load_state('load')

        # Click menu btn and copy as json
        page.click("[data-testid = 'main-menu.button']")
        page.click("[data-testid = 'main-menu-sub.edit-button']")
        page.click("[data-testid='main-menu-sub.copy as-button']")
        page.click("[data-testid='main-menu.copy-as-json']")
        clipboard_content = page.evaluate("navigator.clipboard.readText()")
        json_content = json.loads(clipboard_content)

    except Exception as e:
        raise Exception("Error 01: " + str(e)) 

    page_data = ExtractData(chosen_frame, json_content)

    return page_data


# Loop through the dropdown menu and click the target page
def Dropdown_Checker(chosen_frame, menu):
    for option in menu:
        value = option.inner_text().lower().strip()
        if chosen_frame == value:
            option.click()
            return True
    return False


# Extract the necessary data from the JSON
def ExtractData(chosen_frame: str, content: json):
    frame_id = ''
    desc = ''
    date = ''

    # Leave only the necessary shapes (images, text with names, groups and frames with names)
    content['shapes'] = [shape_data for shape_data in content['shapes'] if (shape_data['type'] == 'frame' and shape_data['props'].get('name', '').strip() != '') or
                         shape_data['type'] == 'image' or
                         (shape_data['type'] == 'text' and shape_data['props'].get('text', '').strip() != '') or
                         shape_data['type'] == 'group']

    # Get the frame id: Still Big(O) = N but half the iteration using 2 pointer
    start_pointer = 0
    end_pointer = len(content['shapes']) - 1
    while start_pointer < end_pointer:
        start_shape = content['shapes'][start_pointer]
        end_shape = content['shapes'][end_pointer]

        # Get frame where all the data is stored and check if the frame is the chosen frame
        if start_shape['type'] == 'frame' and chosen_frame == start_shape['props']['name'].lower().strip() and start_shape['parentId'].startswith('page:'):
            frame_id = content['shapes'][start_pointer]['id']
            break
        elif end_shape['type'] == 'frame' and chosen_frame == end_shape['props']['name'].lower().strip() and end_shape['parentId'].startswith('page:'):
            frame_id = content['shapes'][end_pointer]['id']
            break
        start_pointer += 1
        end_pointer -= 1

    if frame_id == '':
        raise Exception("Error 02: Frame not found. Ensure that the FRAME name matches exactly the PAGE name.")

    frame_desc = get_Frame_Desc(content['shapes'], frame_id)

    # Get the description and date
    if "::" in frame_desc:
        desc, date = frame_desc.split("::")
        desc = desc.strip()
        date = date.strip()
    else:
        raise Exception("Error 03: No description and date found. Ensure that the description is in the format '<description>::<date>'.")

    # Get the student data
    students = get_student_data(content['shapes'], frame_id, content['assets'])
    page_data = {
        'name': chosen_frame,
        'date': date,
        'description': desc,
        'data': students
    } 
    return page_data


# Get the main information of the frame
def get_Frame_Desc(shapes, frame_id):
    frame_desc = ''

    for shape in shapes:
        # Get the frame description and date
        if shape['parentId'] == frame_id and shape['type'] == 'text' and '::' in shape['props']['text']:
            frame_desc = shape['props']['text']
    return frame_desc

# Get student data
def get_student_data(shapes, frame_id, assets,name=None):  
    student_data = {}
    student_imgs = []
    for shape in shapes:
        # Stops here when an image is found and returns the student data
        if shape['parentId'] == frame_id and shape['type'] == 'image':
            img = get_student_img(shape['props']['assetId'], assets)
            student_imgs.append(img)
            
        # Perform a recursive call if its a frame 
        if shape['parentId'] == frame_id and shape['type'] == 'frame':
            name = shape['props']['name']
            student_data.update(get_student_data(shapes, shape['id'],assets, name))

            name = None # Reset the name to None after the recursive call

        # Check if the student is in a group if so, get the grp id and perform a recursive call
        if shape['parentId'] == frame_id and shape['type'] == 'group':
            student_data.update(get_student_data(shapes, shape['id'],assets, name))


    if name is not None:
        student = {
            'image': student_imgs
        }

        # Ensuring that the student_data is not overwritten by duplicate names by checking dictionary keys
        if name in student_data:
            # Append the images to the existing student data
            student_data[name]['image'].extend(student_imgs)
        else:
            student_data[name] = student
    return student_data




def get_student_img(asset_id, assets):
    def convert_img_to_base64_str(img_url):
        response = requests.get(img_url)
        if response.status_code == 200:
            # Convert image to base64 and then decode it to a string.
            # ----Will need to encode it back to bytes when saving it to a file----
            base64_img = base64.b64encode(response.content).decode('utf-8')
            return base64_img
        else:
            return ""

    for asset in assets:
        # Get the student image
        if asset_id == asset['id']:
            base64_img = convert_img_to_base64_str(
                asset['props']['src'])
            return base64_img




def get_all_pages(url, page: Page):
    # Take from menu dropdown list
    page_list = []
    page.goto(url)
    page.wait_for_selector(".tlui-popover")
    page.click(".tlui-button__menu")
    dropdown_menu = page.query_selector('.tlui-page-menu__list')
    page_list = dropdown_menu.inner_text().lower().split("\n")
    return page_list



def loading_screen(curr_frame, stop_loading):
    animation = "|/-\\"
    i = 0
    # While the loading screen is not set (stopped), keep printing the loading screen
    while not stop_loading.is_set():
        sys.stdout.write("\r" + f'Extracting {curr_frame}...' + animation[i % len(animation)]) # Ensure index always within the range of the animation
        sys.stdout.flush()
        time.sleep(0.2)
        i += 1
    
    print("\n" + curr_frame + " completed.")


# Save the data to a json file
def save_data(data, prj_title):
    try:
        with open(f"{prj_title}.json", 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        raise Exception("Error 05:", str(e))

# -----------------End of Functions-----------------#


# -----------------Main Program-----------------#
url = str()
targets = []

while url == "":
    url = input("Tldraw project url: ")


print(Fore.LIGHTMAGENTA_EX +
      "\nType 'ALL' to extract all frames. Otherwise, enter the frame(s) you want to extract." + Fore.RESET)
while True:
    val = input(Fore.LIGHTMAGENTA_EX + "\nWhen finished type 'DONE'.\n:: " + Fore.RESET).lower().strip()

    # Check if the user wants to extract all frames
    if (len(targets) == 0 and val == "all"):
        targets.append(val)
        break

    # Check if the user wants to stop entering frames
    if (val == "done"):
        break

    # Check if the user entered a value
    if (val != ""):
        targets.append(val)


if (len(targets) == 0):
    print(Fore.YELLOW + "No frames selected. Exiting program." + Fore.RESET)
    exit()

# Where all the magic happens
with sync_playwright() as p:
    prj_title = ''
    complete_data = None
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
                                # Add clipboard permissions
                                permissions=["clipboard-read", "clipboard-write"])
    if (targets[0] == "all"):
        # Extract all data, otherwise loop and extract each frame
        page = context.new_page()
        targets = get_all_pages(url, page)
        page.close()
    try:
        complete_data, prj_title = process_pages(url, targets, context)
        save_data(complete_data, prj_title)
    except Exception as e:
        print(Fore.YELLOW + str(e) + Fore.RESET)
        exit()
    
    context.close()
    browser.close()
    print(Fore.GREEN + f"Data successfully extracted and saved as '{prj_title}.json'." + Fore.RESET)
# -----------------End of Main Program-----------------#
