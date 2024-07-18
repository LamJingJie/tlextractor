from colorama import Fore
from playwright.sync_api import sync_playwright, Page, BrowserContext
import json
import requests
import threading
import sys
import time
from PIL import Image
import io
import base64
import os

# Data Structure Example:
# {
#     "project title": "CORE STUDIO 02-24-TEST",
#     "data": [
#         {
#             "page": "benchmark 01",
#             "date": "DUE 26 MAY (SUNDAY) 2359",
#             "description": "First iteration of site in blender/rhino",
#             "students": [
#                 "sean hung xiang hui",
#                 "ooi zher xian",
#                 "kiatkongchayin akrapong"
#             ]
#         }
#     ]
# }

# Example: https://www.tldraw.com/r/fOZmgi9MQzQc-rrXnpAz6?v=-167,-196,5343,2630&p=HGtpLC0ipiTvgK6awql7m

#Video
'''
https://github.com/LamJingJie/tlextractor/assets/58838335/8ea12541-120f-4b0e-8577-770f6d90232a
'''

# -----------------Functions-----------------#

# Process pages chosen by the user
def process_pages(url, targets, context: BrowserContext):
    prj_title = ''
    all_page_data = []

    # Get project title
    page = context.new_page() 
    page.goto(url)
    page.wait_for_selector(".tlui-popover", state='visible')
    page.click(".tlui-button__menu")
    # Try to get the project title, if not found, set it to "Untitled Project"
    try:
        prj_title = page.query_selector(".tlui-top-zone__container").inner_text().strip().replace('\u00a0', ' ').replace('_','-')
    except AttributeError:
        print(Fore.LIGHTCYAN_EX + "Project title not found. Setting it to 'Untitled Project'." + Fore.RESET)
        prj_title = "Untitled Project"

    # Create folder
    folder_name = prj_title + "_images"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    else:
        delete_files(folder_name)
    
    # Loop through each frame and extract the data
    for frame in targets:
        stop_loading = threading.Event()
        loading_thread = threading.Thread(target=loading_screen, args=(frame, stop_loading))
        loading_thread.start() # Start the loading screen
        try:
            page_data = ActivateBot(url, frame, page, folder_name, prj_title)
            all_page_data.append(page_data)
        except Exception as e:
            # This is added to ensure that the loading screen stops and the thread is joined before the program exits
            stop_loading.set()
            loading_thread.join()
            raise Exception("Error 00:",str(e))

        stop_loading.set() # Stop the loading screen
        loading_thread.join() # Wait for the loading screen to finish

    page.close()
    website_data = {
        "project title": prj_title,
        "data": all_page_data
    }

    return website_data, prj_title, folder_name



# playwrite bot for each page
def ActivateBot(url, chosen_frame, page: Page, folder_name, prj_title):
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

    page_data = ExtractData(chosen_frame, json_content, folder_name, prj_title)

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
def ExtractData(chosen_frame: str, content: json, folder_name, prj_title):
    frame_id = ''
    desc = ''
    date = ''
    isCustomTemplatePresent = False

    # Leave only the necessary shapes (images, text with names, groups and frames with names, submission frame template)
    content['shapes'] = [shape_data for shape_data in content['shapes'] 
                         if (shape_data['type'] == 'frame' and 
                            shape_data['props'].get('name', '').strip() != '') or
                            shape_data['type'] == 'image' or
                            (shape_data['type'] == 'text' and shape_data['props'].get('text', '').strip() != '') or
                            shape_data['type'] == 'group' or
                            shape_data['type'] == 'submission_frame'
                        ]
    

    # Get the frame id: Still Big(O) = N but half the iteration using 2 pointer
    start_pointer = 0
    end_pointer = len(content['shapes']) - 1
    while start_pointer <= end_pointer:
        start_shape = content['shapes'][start_pointer]
        end_shape = content['shapes'][end_pointer]

        # Check if the custom template is present
        if start_shape['type'] == 'submission_frame':
            isCustomTemplatePresent = True
        elif end_shape['type'] == 'submission_frame':
            isCustomTemplatePresent = True

        # Get frame where all the data is stored and check if the frame is the chosen frame
        if start_shape['type'] == 'frame' and chosen_frame == start_shape['props']['name'].lower().strip() and start_shape['parentId'].startswith('page:'):
            frame_id = content['shapes'][start_pointer]['id']
        elif end_shape['type'] == 'frame' and chosen_frame == end_shape['props']['name'].lower().strip() and end_shape['parentId'].startswith('page:'):
            frame_id = content['shapes'][end_pointer]['id']
            
        start_pointer += 1
        end_pointer -= 1

    if frame_id == '':
        raise Exception("Error 02: Frame not found. Ensure that the FRAME name matches exactly the PAGE name.")

    frame_desc = get_Frame_Desc(content['shapes'], frame_id)

    # Get the description and date
    if "::" in frame_desc:
        desc, date = frame_desc.split("::")
        desc = desc.strip()
        date = date.strip().replace('<', '').replace('>', '')
    else:
        desc = 'desc'
        date = 'date'
        print(Fore.LIGHTCYAN_EX + "No description and date found. Setting it to default value. Ensure that the description is in the format '<description>::<date>'." + Fore.RESET)
        #raise Exception("Error 03: No description and date found. Ensure that the description is in the format '<description>::<date>'.")
    

    # Use different methods depending on the custom template presence
    # Only students that have submitted will be included
    if(isCustomTemplatePresent):
        students = get_student_data_method2(content['shapes'], frame_id, content['assets'], folder_name, date, prj_title, chosen_frame)
    else:
        students = get_student_data_method1(content['shapes'], frame_id, content['assets'], folder_name, date, prj_title, chosen_frame)

    
    page_data = {
        'page': chosen_frame,
        'date': date,
        'description': desc,
        'students': students
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



# Get student data recursively by assuming that the student's image is always in the frame and that frame has the student name
# Utilizing DFS algorithm
# Method 1: No custom template
def get_student_data_method1(shapes, frame_id, assets, folder_name, date, prj_title, chosen_frame, name=None):  
    student_names = set() # Only keep unique names
    has_student_imgs = False
    for shape in shapes:

        # Stops here when an image is found and returns the student data
        if shape['parentId'] == frame_id and shape['type'] == 'image' and name is not None:
            get_student_img(shape['props']['assetId'], assets, folder_name, name, date, prj_title, chosen_frame)
            has_student_imgs = True
            
        # Perform a recursive call if its a frame 
        if shape['parentId'] == frame_id and shape['type'] == 'frame':
            name = shape['props']['name'].strip().replace('<', '').replace('>', '')
            student_names.update(get_student_data_method1(shapes, shape['id'],assets, folder_name, date, prj_title, chosen_frame, name))

            name = None # Reset the name to None after the recursive call

        # Check if the student is in a group if so, get the grp id and perform a recursive call
        if shape['parentId'] == frame_id and shape['type'] == 'group':
            student_names.update(get_student_data_method1(shapes, shape['id'],assets, folder_name, date, prj_title, chosen_frame, name))


    if name is not None and has_student_imgs:
        student_names.add(name)

    return list(student_names)


# Get student data, if any frame or group perform recursion until it reaches the custom template type
# Utilizing DFS algorithm
# Method 2: Custom template
def get_student_data_method2(shapes, frame_id, assets, folder_name, date, prj_title, chosen_frame, name = None):
    student_names = set() # Only keep unique names
    has_student_imgs = False
    for shape in shapes:
        # Stops here when an image is found and its inside the submission_frame
        if shape['parentId'] == frame_id and shape['type'] == 'image' and name is not None:
            get_student_img(shape['props']['assetId'], assets, folder_name, name, date, prj_title, chosen_frame)
            has_student_imgs = True

        # Perform a recursive call and send over the student name
        if shape['type'] == 'submission_frame' and shape['parentId'] == frame_id:
            name = shape['props']['name'].strip().replace('<', '').replace('>', '')
            student_names.update(get_student_data_method2(shapes, shape['id'], assets, folder_name, date, prj_title, chosen_frame, name))

            name = None
        
        if (shape['type'] == 'group' or shape['type'] == 'frame') and shape['parentId'] == frame_id:
            # Perform a recursive call if its a group or frame, each time going deeper
            student_names.update(get_student_data_method2(shapes, shape['id'], assets, folder_name, date, prj_title, chosen_frame, name))
    
    if name is not None and has_student_imgs:
        student_names.add(name)

    return list(student_names)

    


# Get the student image and save it in a seperate folder
def get_student_img(asset_id, assets, folder_name, student_name, date, prj_title, chosen_frame):

    # Resize img and save it in seperate folder
    def img_resize_and_save(img_url):
        Image.MAX_IMAGE_PIXELS = None

        # Check if the image is a base64 image rather than a url
        if(img_url.startswith('data:image') and img_url.find('base64,')):
            base64_index = img_url.find('base64,') + len('base64,')
            # Decode everything after the base64, to get the image data
            image_data = base64.b64decode(img_url[base64_index:])
            img = Image.open(io.BytesIO(image_data))
        else:
            response = requests.get(img_url)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
            else:
                raise Exception("Error 04: Image not found. Exiting program.")

        # Resize the image if it exceeds the max resolution on either x or y axis
        try:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            max_reso_x_y = 4096

            if img.width > max_reso_x_y:
                new_width = max_reso_x_y
                img = img.resize((new_width, img.height),
                               Image.Resampling.LANCZOS)  # Smooth the img

            if img.height > max_reso_x_y:
                new_height = max_reso_x_y
                img = img.resize((img.width, new_height),
                                 Image.Resampling.LANCZOS)  # Smooth the img

            # Save Image with incremental unique id, prevent overwriting
            uniqueid = 1
            img_name = ""
            while img_name == "" or os.path.exists(save_path):
                img_name = prj_title + "___" + chosen_frame + "___" + date + \
                        "___" + student_name + "___" + str(uniqueid) + ".png"
                save_path = os.path.join(folder_name, img_name)
                uniqueid += 1

            img.save(save_path, format='PNG') #Err here

        except Exception as e:
            raise Exception("Error 04:", str(e))


    for asset in assets:
        # Get the student image
        if asset_id == asset['id']:
            img = asset['props']['src']           
            img_resize_and_save(img)



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
        time.sleep(0.15)
        i += 1
    
    print("\n" + curr_frame + " completed.")



def delete_files(folder_name):
    for filename in os.listdir(folder_name):
        file_path = os.path.join(folder_name, filename)
        try:
            os.unlink(file_path)
        except Exception as e:
            raise Exception(f"Error 06: Failed to delete '{file_path}' because '{e}'")



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
    folder_name = ''
    complete_data = None
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
                                # Add clipboard permissions
                                permissions=["clipboard-read", "clipboard-write"],
                                )
    if (targets[0] == "all"):
        # Extract all data, otherwise loop and extract each frame
        page = context.new_page()
        targets = get_all_pages(url, page)
        page.close()
    try:
        complete_data, prj_title, folder_name = process_pages(url, targets, context)
        save_data(complete_data, prj_title)
    except Exception as e:
        print(Fore.LIGHTYELLOW_EX + str(e) + Fore.RESET)
        exit()
    
    context.close()
    browser.close()
    print(Fore.LIGHTGREEN_EX + f"Data successfully extracted and saved at '{prj_title}.json' and '{folder_name}' folder" + Fore.RESET)
# -----------------End of Main Program-----------------#
