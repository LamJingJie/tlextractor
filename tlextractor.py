import os
os.environ['PYPPETEER_CHROMIUM_REVISION'] = '1230501'


from colorama import Fore


# TASKS
# - Change to playwright for better performance


url = str()
target = []
val = str()

# Example: https://www.tldraw.com/r/eRZwoL-G5ufBB3KTRaSbW?v=-659,-888,5720,4826&p=HGtpLC0ipiTvgK6awql7m
#pattern = "^http(s|):\/\/[0-9A-z.]+.[0-9A-z/.]+$"
#tlui-button__menu



# Extract data from the url
def ExtractData(frame):
    # if url is invalid, exit program
    
    try:
        pass
    except Exception as e:
        print(Fore.RED + str(e))
        exit()





while url == "":
    url = input("Tldraw project url: ")


print(Fore.LIGHTCYAN_EX + "\nType 'ALL' to extract all frames. Otherwise, enter the frame(s) you want to extract.")
while True:
    val = input("\nWhen finished type 'DONE'.\n::").lower()

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




if (target[0] == "all"):
    # Extract all data
    pass
else:
    if (len(target) == 0):
        print(Fore.RED + "No frames selected. Exiting program.")
        exit()

    # loop and extract each frame
    for i in target:
        ExtractData(i)

    



