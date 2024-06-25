# TLExtractor

TLExtractor is a Python script designed to extract specific data from pages from tldraw. It uses a template to ensure the accuracy of the data being extracted. Data extracted will be saved as JSON data while images will be stored in a seperate folder that is titled the same as the project title.

## Template Format

The script requires the data to be in a specific format:

* The text that includes the page description and date should be in this format: `<description>::<date>`. It must be nested at the main frame only.
* Use only frames to 'group' things together.
* Ensure the main frame name is the exact same as the page name.
* Submissions for every person should be framed respectively with their names.

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

<a href="https://github-production-user-asset-6210df.s3.amazonaws.com/58838335/340716156-68d26e9a-b312-4af8-9200-c902aa7527f3.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20240618%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240618T143126Z&X-Amz-Expires=300&X-Amz-Signature=38cc577f04cab4a33903b9ba850aceb69ce931e4fda028dd33d43ce8678bd1cb&X-Amz-SignedHeaders=host&actor_id=58838335&key_id=0&repo_id=813742945" target="_blank"><img src="https://github-production-user-asset-6210df.s3.amazonaws.com/58838335/340716156-68d26e9a-b312-4af8-9200-c902aa7527f3.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20240618%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240618T143126Z&X-Amz-Expires=300&X-Amz-Signature=38cc577f04cab4a33903b9ba850aceb69ce931e4fda028dd33d43ce8678bd1cb&X-Amz-SignedHeaders=host&actor_id=58838335&key_id=0&repo_id=813742945" 
alt="IMAGE ALT TEXT HERE" width="240" height="180" border="10" /></a>
