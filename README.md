# TLExtractor

TLExtractor is a Python script designed to extract specific data from pages from tldraw. It uses a template to ensure the accuracy of the data being extracted. Data extracted will be saved as JSON data while images will be stored in a seperate folder that is titled the same as the project title.

## Template Format

The script requires the data to be in a specific format:

* The text that includes the page description and date should be in this format: `<description>::<date>`. It must be nested at the main frame only.
* Use only frames to 'group' things together.
* Ensure the main frame name is the exact same as the page name.
* Submissions for every person should be framed together with their names in that frame.

#### Template 1 - For 1 submission per student
![Template Format 1](./img/template_format1.png)

#### Template 2 - For 1> submissions per student
![Template Format 2](/img/template_format2.png)

#### Template 3 - For multiple nested groupings
![Template Format 2](/img/template_format3.png)

## Prerequisites

Before you begin, ensure you have met the following requirements:

* You have installed the latest version of [pipenv](https://pipenv.pypa.io/en/latest/) and [pip](https://pypi.org/project/pip/#history).
* You are using a `Python 3.x` version.

## Installation

To install TLExtractor, follow these steps:

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
