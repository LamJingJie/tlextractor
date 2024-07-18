# TLExtractor

TLExtractor is a Python script designed to extract specific data from tldraw pages. It utilizes a template to ensure data accuracy. Extracted data is saved as JSON, while images are stored in a folder named after the project title. This script accommodates two scenarios: the **standard tldraw** and **tldraw with a custom submission template**, each with unique but similar designs.

For more information on the **custom submission template**, visit:
[Custom Submission Template](https://github.com/LamJingJie/tldraw/tree/dynamic_submission_template/templates/vite)

## Template Format

The script requires data in a specific format:

- Text including the page description and date should follow the format: `<description>::<date>`, nested in the main frame only.
- Only use 'frames' or 'groups' for grouping.
- The main frame name must match the page name exactly.
- For **standard tldraw**, frame each person's submissions together, including their names in the frame.
- Avoid special characters.

### Template Examples

#### Template 1: For 1 submission per student

![Template Format 1](./img/template_format1.png)

#### Template 2: For multiple submissions per student

![Template Format 2](/img/template_format2.png)

#### Template 3: For multiple nested groupings

![Template Format 3](/img/template_format3.png)

#### Template 4: For custom submission template

![Template Format 4](/img/template_format4.png)

## Prerequisites

Before starting, ensure you have:

- Installed the latest versions of [pipenv](https://pipenv.pypa.io/en/latest/) and [pip](https://pypi.org/project/pip/#history).
- A `Python 3.x` environment.

## Installation

To install TLExtractor:

1. Clone the repository or download the source code.
2. Navigate to the project directory.
3. Install the virtual environment:

   ```bash
   pip install pipenv
    ```

4. Activate the virtual environment:

    ```bash
    pipenv shell
    ```

5. Install the project dependencies:

    ```bash
    pipenv install
    ```

## Usage

To use TLExtractor, follow these steps:

```bash
python tlextractor.py
```

## Demo Video

<a href="https://github.com/LamJingJie/tlextractor/assets/58838335/8ea12541-120f-4b0e-8577-770f6d90232a" target="_blank"><img src="https://github.com/LamJingJie/tlextractor/assets/58838335/8ea12541-120f-4b0e-8577-770f6d90232a"
alt="IMAGE ALT TEXT HERE" width="240" height="180" border="10" /></a>
