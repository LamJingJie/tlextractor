from colorama import Fore
from playwright.sync_api import sync_playwright, Page, BrowserContext
import json
import threading
import sys
import time
from PIL import Image
import io
from concurrent.futures import ThreadPoolExecutor
import base64
import os
import requests
from multiprocessing import Lock, Pool, Manager, cpu_count
import queue
from yarl import URL

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

# TASKS:
# Use Threading first when initializing pages
# afterwards, use async and multi-processing for each of the images in their respective pages (ensure each image has unique name)

#Video
'''
https://github.com/user-attachments/assets/dc9f5a26-42ee-4a25-8939-9bdc7ec75dfa
'''

# -----------------Functions-----------------#

# Global Variable
all_page_data = []
data_lock = threading.Lock()
console_lock = threading.Lock()
exception_queue_threads = queue.Queue()

# Track all the images that have been processed to prevent duplicates, use manager to share across processes
# because processes do not share memory space
images_obj_tracker = None 
image_lock = None
pool = None # multi-processing pool

# -----------------Main Functions-----------------#
# Process pages chosen by the user
def process_pages(url, targets, context: BrowserContext):
    global pool, all_page_data, images_obj_tracker, image_lock

    stop_loading = threading.Event()
    setup_thread = threading.Thread(target=setting_up_screen, args=(stop_loading,))
    setup_thread.start()  # Start the loading screen

    # Initializing the multi-processing pool
    manager = Manager()
    pool = Pool(processes=20) # <-- Change depending on ur system*
    images_obj_tracker = manager.dict()
    image_lock = manager.Lock()

    prj_title = ''
    pages_threads = []

    # Get project titles
    page = context.new_page()
    try:
        page.goto(url)
    except Exception as e:
        stop_loading.set()
        setup_thread.join()
        raise Exception(Fore.LIGHTYELLOW_EX + "Program Start: " + str(e) + Fore.RESET)
    
    page.wait_for_selector(".tlui-popover", state='visible')

    # Try to get the project title, if not found, set it to "Untitled Project"
    try:
        prj_title = page.query_selector(".tlui-top-panel__container").inner_text().strip().replace('\u00a0', ' ').replace('_','-')
    except AttributeError as a:
        print(Fore.LIGHTCYAN_EX + "Project title not found. Setting it to 'Untitled Project'." + Fore.RESET)
        prj_title = "Untitled Project"
    page.close()

    # Create folder
    folder_name = prj_title + "_images"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    else:
        delete_files(folder_name)
    
    stop_loading.set()
    setup_thread.join()
 
    # Loop through each frame and extract the data
    # Get the thread ready and after all has been initialized, start executing the threads. Order determined by OS
    print("\n\nExtracting data from the following pages:")
    rows = 4
    for frame in targets:
        individual_page_thread = threading.Thread(target=run_individual_page, args=(rows, url, frame, folder_name, prj_title)) 
        individual_page_thread.start()
        pages_threads.append(individual_page_thread)
        rows+=1


    # Wait for all threads to finish
    for thread in pages_threads:
        thread.join()

   
    # Move to right below the threads
    move_cursor(rows + 2, 1)

    
    website_data = {
        "project title": prj_title,
        "data": all_page_data
    }

    sys.stdout.write("\rImage currently being processed, dont exit! This may take a while...")

    return website_data, prj_title, folder_name


# Utilize threading to extract data from each page
def run_individual_page(row, url, frame, folder_name, prj_title):
    global all_page_data, data_lock

    stop_loading_success = threading.Event()
    stop_loading_failure = threading.Event()
    loading_thread = threading.Thread(target=loading_screen, args=(row, frame, stop_loading_success, stop_loading_failure))
    loading_thread.start()  # Start the loading screen

    try:
        page_data = ActivateBot(url, frame, folder_name, prj_title)
        # Lock the data to prevent race conditions and data corruption by multiple threads
        with data_lock:
            all_page_data.append(page_data)

    except Exception as e:
        # This is added to ensure that the loading screen stops and the thread is joined before the program exits
        stop_loading_failure.set()
        loading_thread.join()
        exception_queue_threads.put(f"{frame}--> {e}")
    

    stop_loading_success.set()  # Stop the loading screen
    # Wait for the loading screen to finish before going to the next frame/page
    loading_thread.join()

    

# playwrite bot for opening of each page
def ActivateBot(url, chosen_frame, folder_name, prj_title):
    tldraw_menu_list = '.tlui-page-menu__list'
    tldraw_menu_item = '.tlui-page-menu__item'
    try:
        # Ensure that each thread creates a new page to prevent errs
        with sync_playwright() as p:
        
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                                    # Add clipboard permissions
                                    permissions=["clipboard-read", "clipboard-write"],
                                    )
            page = context.new_page()
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
    global pool
    for asset in assets:
        # Get the student image in the assets array
        if asset_id == asset['id']:
            img = asset['props']['src']

            # Run image resizing in multi-processing by submitting tasks inside hehe
            pool.apply_async(img_resize_save, args=(img, folder_name, student_name, date, prj_title, chosen_frame, images_obj_tracker, image_lock))
            break
            

# Resize img and save it in seperate folder
def img_resize_save(img_url: URL | str, folder_name, student_name, date, prj_title, chosen_frame, img_tracker_dict, img_lock):

    Image.MAX_IMAGE_PIXELS = None
    # Check if the image is a base64 image rather than a url
    if (img_url.startswith('data:image') and img_url.find('base64,')):
        base64_index = img_url.find('base64,') + len('base64,')
        # Decode everything after the base64, to get the image data
        img_data = base64.b64decode(img_url[base64_index:])
    else:
        response = requests.get(img_url)
        if response.status_code == 200:
            img_data = response.content
        else:
            raise Exception("Error 04: Image not found. Exiting program.")

    # Write bytes into memory temporarily and use it to open the img
    img = Image.open(io.BytesIO(img_data))

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
        img_name = prj_title + "___" + chosen_frame + "___" + date + \
            "___" + student_name + "___"

        with img_lock:
            img_tracker_dict[img_name] = img_tracker_dict.get(img_name, 0) + 1

        img_name += str(img_tracker_dict[img_name]) + '.png'
        save_path = os.path.join(folder_name, img_name)
        img.save(save_path, format='PNG')

    except Exception as e:
        raise Exception("Error 04:", str(e))

# ------------End Of Main Functions----------------- #

# ------------Side Functions----------------- #

# Loop through the dropdown menu and click the target page
def Dropdown_Checker(chosen_frame, menu):
    for option in menu:
        value = option.inner_text().lower().strip()
        if chosen_frame == value:
            option.click()
            return True
    return False



def get_all_pages(url, page: Page):
    # Take from menu dropdown list
    page_list = []
    try:
        page.goto(url)
        page.wait_for_selector(".tlui-popover")
        page.click(".tlui-button__menu")
        dropdown_menu = page.query_selector('.tlui-page-menu__list')
        page_list = dropdown_menu.inner_text().lower().split("\n")
        return page_list
    except Exception as e:
        print(Fore.LIGHTYELLOW_EX + "Program Start: " + str(e) + Fore.RESET)
        exit()



# Move the cursor to the specified row and column in the terminal
def move_cursor(row, col):
    sys.stdout.write(f"\033[{row};{col}H")



# Clear the terminal screen
def clear_screen():
    sys.stdout.write("\033[2J")
    sys.stdout.flush()



def setting_up_screen(stop_loading):
    while not stop_loading.is_set():
        sys.stdout.write("\rSetting up the system...")
    sys.stdout.write("\rSystem setup complete.")



def loading_screen(row, curr_frame, stop_loading_success, stop_loading_failure):
    global console_lock

    line_length = 10
    position = 0

    # While the loading screen is not set (stopped), keep printing the loading screen
    while not stop_loading_success.is_set() and not stop_loading_failure.is_set():
        line = ['.' for _ in range(line_length)]
        line[position % line_length] = '|'
        line = "".join(line)

        # Prevent overlapping the loading screen with other threads, making sure that row is dedicated to 1 thread
        with console_lock:
            move_cursor(row, 1)
            sys.stdout.write("\r" + f'Extracting {curr_frame}' + line) # Ensure index always within the range of the animation
            sys.stdout.flush()
        time.sleep(0.1)
        position += 1
    

    with console_lock:  
        # Move the cursor to the same row and override the loading screen with final msg
        move_cursor(row, 1)
        if(stop_loading_failure.is_set()):
            sys.stdout.write("\r\033[K" + Fore.LIGHTRED_EX + "\r" + curr_frame + " failed. Exiting program." + Fore.RESET)
        else:
            sys.stdout.write("\r\033[K" + Fore.LIGHTGREEN_EX + "\r" + curr_frame + " extracted successfully." + Fore.RESET)



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

# ------------End Of Side Functions----------------- #

# -----------------End of Functions-----------------#


# -----------------Main Program-----------------#
def main(targets):
    global pool
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
            print("\n" + Fore.LIGHTYELLOW_EX + str(e) + Fore.RESET + "\n")
            context.close()
            browser.close()
            pool.close()
            pool.join()
            exit()
    
        context.close()
        browser.close()

        # Close the pool of multi-processors
        pool.close()
        pool.join()

        if not exception_queue_threads.empty():
            while not exception_queue_threads.empty():
                e = exception_queue_threads.get()
                sys.stdout.write("\r\033[K" + Fore.LIGHTYELLOW_EX + f"\r{e}\n" + Fore.RESET)
        else:
            sys.stdout.write("\r\033[K" + Fore.LIGHTGREEN_EX + f"\rData successfully extracted and saved at '{prj_title}.json' and '{folder_name}' folder" + Fore.RESET)



if __name__ == "__main__":
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
        print(Fore.LIGHTYELLOW_EX + "No frames selected. Exiting program." + Fore.RESET)
        exit()
    clear_screen()
    move_cursor(1, 1)
    main(targets)
    
        
# -----------------End of Main Program-----------------#
