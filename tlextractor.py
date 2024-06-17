from colorama import Fore
from playwright.sync_api import sync_playwright, Page
import json
import base64
import requests

url = str()
target = []
val = str()

# Tasks
# 1. Test the program with multiple frames
# 2. Add functionality for when the user selects "ALL"

## Data Structure
'''[
    {
        "name": "benchmark 01",
        "date": "DUE 26 MAY (SUNDAY) 2359",
        "description": "First iteration of site in blender/rhino",
        "data": [
            {
                "subtitle": "The Proto-Cementary",
                "students": [
                    {
                    "name": "Jia Wei",
                    "image": ["base64_img", "base64_img"]
                    },
                ]
            }
        ]
    }
]'''

## Example: https://www.tldraw.com/r/fOZmgi9MQzQc-rrXnpAz6?v=-167,-196,5343,2630&p=HGtpLC0ipiTvgK6awql7m

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

        if(not Dropdown_Checker(chosen_frame, dropdown_menu)):
            print(Fore.YELLOW + "Page not found. Exiting program." + Fore.RESET)
            exit()
        page.wait_for_load_state('load')

        # Click menu btn and copy as json
        page.click("[data-testid = 'main-menu.button']")
        page.click("[data-testid = 'main-menu-sub.edit-button']")
        page.click("[data-testid='main-menu-sub.copy as-button']")
        page.click("[data-testid='main-menu.copy-as-json']")
        clipboard_content = page.evaluate("navigator.clipboard.readText()")
        json_content = json.loads(clipboard_content)
        
    except Exception as e:
        print(Fore.YELLOW + str(e) + Fore.RESET)                           
        exit()

    page_data = ExtractData(chosen_frame, json_content)
    return page_data


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
    desc = ''
    date = ''
    students = []

    # Remove all shapes that are type ='geo'
    content['shapes'] = [shape_data for shape_data in content['shapes'] if shape_data['type'] != 'geo']

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

    frame_desc, subtitles = get_main_info(content['shapes'], frame_id)

    # Get the description and date
    if "::" in frame_desc:
        desc, date = frame_desc.split("::")
        desc = desc.strip()
        date = date.strip()
    else:
        print(Fore.YELLOW + "Please write your text to be '<description>::<date>'. Exiting program." + Fore.RESET)
        exit()

    # Get the student data
    students = get_student_data(content, subtitles)
    page_data = {
        'name': frame,
        'date': date,
        'description': desc,
        'data': students
    }
    return page_data





# Get the main information of the frame
def get_main_info(shapes, frame_id):
    frame_desc = ''
    subtitles = []

    for shape in shapes:
        # Get the frame description and date
        if shape['parentId'] == frame_id and shape['type'] == 'text':
            frame_desc = shape['props'].get('text', '')
        
        #Get subtitles id and name
        if shape['parentId'] == frame_id and shape['type'] == 'frame':
            subtitle = {
                'id': shape['id'],
                'name': shape['props'].get('name', '')
            }
            subtitles.append(subtitle)

    if len(subtitles) == 0:
        print(Fore.YELLOW + "No subtitles found. Exiting program." + Fore.RESET)
        exit()
    return frame_desc, subtitles



def get_student_data(content: json, subtitles):
    student_data = [] # Stores each of the subtitle names and its students
    
    student_name = ''
    student_img = []
    shapes = content['shapes']

    for subtitle in subtitles:
        subtitle_students = []

        for shape in shapes:
            # Get the student name for each subtitle
            if subtitle['id'] == shape['parentId'] and shape['type'] == 'frame':
                student_id = shape['id']
                student_name = shape['props'].get('name', '')
                student_asset_id = get_img_assetID(student_id, content['shapes']) #Array of student image asset id
                student_img = get_student_img(student_asset_id, content['assets']) #Array of student image
                student = {
                    'name': student_name,
                    'image': student_img
                }
                subtitle_students.append(student)
        
        subtitle = {
            'subtitle': subtitle['name'],
            'students': subtitle_students
        }
        student_data.append(subtitle) # Main data is stored here

    return student_data
                
                    


def get_img_assetID(student_id, shapes):
    student_asset_id = []
    for shape in shapes:
        # Get the student image asset id
        if student_id == shape['parentId'] and shape['type'] == 'image':
            student_asset_id.append(shape['props']['assetId']) 
    return student_asset_id


def get_student_img(asset_id, assets):
    student_img = []
    if len(asset_id) != 0:
        for id in asset_id:
            for asset in assets:
                # Get the student image
                if id == asset['id']:
                    base64_img = convert_img_to_base64_str(asset['props']['src'])
                    student_img.append(base64_img)
                    break
    return student_img


def convert_img_to_base64_str(img_url):
    response = requests.get(img_url)
    if response.status_code == 200:
        # Convert image to base64 and then decode it to a string.
        # ----Will need to encode it back to bytes when saving it to a file----
        base64_img = base64.b64encode(response.content).decode('utf-8')
        return base64_img
    else:
        return ""


def save_data(page_data):
    try:
        with open("tldraw_data.json", 'w') as file:
            json.dump(page_data, file, indent=4)
    except Exception as e:
        print(Fore.YELLOW + str(e) + Fore.RESET)
        exit()




while url == "":
    url = input("Tldraw project url: ")


print(Fore.LIGHTMAGENTA_EX + "\nType 'ALL' to extract all frames. Otherwise, enter the frame(s) you want to extract." + Fore.RESET)
while True:
    val = input(Fore.LIGHTMAGENTA_EX+"\nWhen finished type 'DONE'.\n:: " + Fore.RESET).lower().strip()

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
    website_data = []
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(permissions=["clipboard-read", "clipboard-write"]) # Add clipboard permissions
    if (target[0] == "all"):
        # Extract all data
        pass
    else:
        # loop and extract each frame
        for frame in target:
            page = context.new_page()
            website_data.append(ActivateBot(url, frame, page))
    save_data(website_data)
    context.close()
    browser.close()


    



