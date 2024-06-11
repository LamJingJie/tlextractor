from urllib.request import urlopen
import re



url = str()
target = []
val = str()
#pattern = "^http(s|):\/\/[0-9A-z.]+.[0-9A-z/.]+$"

# Extract data from the url
def ExtractData():
    # page = urlopen(url)
    pass





# 1. add url checker in the future
while url == "":
    url = input("Tldraw project url: ")

while True:
    val = input("\n\nType 'ALL' first to extract all frames.\nOtherwise, enter the frame(s) you want to extract. When finished type 'DONE'.\n::").lower()

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
    # loop and extract each frame

    pass

print("Target: \n", target)



