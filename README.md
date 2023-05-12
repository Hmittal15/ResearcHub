# ResearcHub

## Introduction
ResearcHub is an application that allows users to scrape data from Springer and retrieve documents of interest. It also provides several features such as summarization, translation, and recommendations based on the retrieved documents. The application also allows users to query the documents for information.

This project aims to make it easier for users to retrieve and analyze academic documents by providing a range of features to enhance the user's experience and increase the accessibility of the documents.

Technologies used in this project
* Streamlit
* AWS S3
* Apache Airflow
* Docker
* Google Cloud Platform
* FastAPI
* Great Expectations

## Architecture diagram
![deployment_architecture_diagram](https://user-images.githubusercontent.com/108916132/235260615-d93723bb-91ca-4f2e-b723-427f6b53d6f0.png)

## Installation

To clone and replicate the repository, please follow the steps below:

1.  Open the command line interface (CLI) on your computer.
2.  Navigate to the directory where you want to clone the repository.
3.  Type `git clone <repo lonk>` and press Enter. This will clone the repository to your local machine.
4.  Navigate into the cloned repository using `cd your-repo`
5.  Set environment variables as mentioned below.
6.  Navigate to 'streamlit' directory and run the command `streamlit run video.py`

#### Environment variables:

* PINECONE_API_KEY = "your_key_here"
* PINECONE_ENV = "your_key_here"
* PINECONE_API_KEY_DOC = "your_key_here"
* PINECONE_ENV_DOC = "your_key_here"
* AWS_ACCESS_KEY = "your_key_here"
* AWS_SECRET_KEY = "your_key_here"
* USER_BUCKET_NAME =  "your_key_here"
* AWS_REGION =  "your_key_here"
* OPENAI_ACCESS_KEY = "your_key_here"
* RAPID_API_HOST = "your_key_here"
* RAPID_API_KEY = "your_key_here"

## Technical documents:
https://docs.google.com/document/d/1-GWEz08lyZdIzqKjxUH_mkB46KBEHLkUl31T9X-kV1Y/edit?usp=sharing

## Application public link:
34.75.99.189:8000/

## Airflow DAGs:
http://34.75.99.189:8080/

## Codelab document:
https://codelabs-preview.appspot.com/?file_id=1-GWEz08lyZdIzqKjxUH_mkB46KBEHLkUl31T9X-kV1Y#0

## Attestation:
WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK
Contribution:
* Ananthakrishnan Harikumar: 25%
* Harshit Mittal: 25%
* Lakshman Raaj Senthil Nathan: 25%
* Sruthi Bhaskar: 25%
