# TLExtractor

TLExtractor is a Python script designed to extract specific students datas from tldraw pages. It utilizes a template that students have to submit to for their projects, and must be followed in order to ensure data accuracy of this script. Extracted data is saved as JSON, while processed images (resizing) are stored in a folder named after the project title. 

This script accommodates two scenarios: the **standard tldraw** and **tldraw with a custom submission template**, each with unique but similar designs.

</br>

## 📄 Custom Submission Template

For more information on the **custom submission template**, visit:
[Custom Submission Template](https://github.com/LamJingJie/tldraw/tree/dynamic_submission_template)

</br>

## ✨ Features

- **🔍 Depth-first Search**:
  - Utilized for data searching and saving.

- **⚡ Async**:
  - Creates multiple coroutine objects depending on the number of pages.  
  - Runs concurrently using Event Loop.
  - Uses Async Playwright to extract data.

- **⚙️ Multi-Processing**:
  - Process multiple recursion functions. Retrieve student names that submitted their project.
  - Processes multiple images, especially useful when there are many images to process.
  - Multi-Processing (17) is nested inside Async as the start is more I/O intensive and the end is more CPU intensive.

- **🧵 Multi-Threading**:
  - Creates as many loading threads as there are coroutine objects.
  - Simulates loading screen.

</br>

## 📋 Template Format

The script requires data in a specific format:

#### General
- Text including the page description and date should follow the format: `<description>::<date>`, nested in the main/outermost frame only.
- Only use 'frames' or 'groups' for grouping.
- The main/outermost frame name must match the page name exactly.
- Avoid special characters.

#### For Standard Tldraw Only
- **Student Submissions**: 
  - Images inside the main 'frame' are assumed to be student submissions. 
  - `Do not` carelessly put images inside otherwise.

- **Frame Titles**: 
  - The title of the 'frame' is assumed to be the student's name.
  - Only saved when it has an image encased inside.
  - Always ensure that the 'frame' encasing all of a student's submissions has the student's name as its title.

- **Nested Frames**: 
  - Do not have nested 'frames' of submissions that are already inside the student frame.
  - 'Grouping' them, however, is fine.

</br>

#### 🖼️ Template Examples

| Template | Description |
|----------|-------------|
| **Template 1** | For 1 submission per student |
| ![Template Format 1](./img/template_format1.png) | |
| **Template 2** | For multiple submissions per student |
| ![Template Format 2](/img/template_format2.png) | |
| **Template 3** | For multiple nested groupings |
| ![Template Format 3](/img/template_format3.png) | |
| **Template 4** | For custom submission template |
| ![Template Format 4](/img/template_format4.png) | |

</br></br>

## 🛠️ Prerequisites

Before starting, ensure you have:

- Installed the latest versions of [pipenv](https://pipenv.pypa.io/en/latest/) and [pip](https://pypi.org/project/pip/#history).
- A `Python 3.x` environment.

</br>

## 🚀 Installation

To install TLExtractor:

1. Clone the repository or download the source code.
2. Navigate to the project directory.
3. Install the virtual environment (for ease of dependencies installation):

    ```bash
    pip install pipenv
    ```

4. Add SCRIPT directory to environment PATH

    ```bash
    C:\Users\<username>\AppData\Local\Packages\PythonSoftwareFoundation\LocalCache\local-packages\Python312\Scripts
    ```

4. Activate the virtual environment:

    ```bash
    pipenv shell
    ```

5. Install the project dependencies:

    ```bash
    pipenv install
    ```
</br>

## Usage

To use TLExtractor, follow these steps:

```bash
python tlextractor.py
```

## 🎥 Demo Video

[![Demo Vid](https://github.com/user-attachments/assets/dc9f5a26-42ee-4a25-8939-9bdc7ec75dfa)](https://github.com/user-attachments/assets/dc9f5a26-42ee-4a25-8939-9bdc7ec75dfa)
