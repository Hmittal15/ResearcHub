[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![DockerHub](https://img.shields.io/badge/DockerHub-0db7ed?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![GCP](https://img.shields.io/badge/GCP-4285F4?style=flat-square&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![AWS S3](https://img.shields.io/badge/AWS_S3-232F3E?style=flat-square&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/s3/)
[![Great Expectations](https://img.shields.io/badge/Great_Expectations-00778B?style=flat-square&logo=great-expectations&logoColor=white)](https://greatexpectations.io/)
[![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-007A88?style=flat-square&logo=apache-airflow&logoColor=white)](https://airflow.apache.org/)


# ResearcHub

## Introduction
ResearcHub is a one-stop solution for any research enthusiast! We have consolidated all the research papers, journals, book PDFs, all at one place. It also provides several convenience features such as summarization, translation, and recommendations for the user selected documents. The application also allows users to query the document itself for any specific information, instead of skimming through long documents. This project aims to make it easier for users to retrieve and analyze academic documents by providing a range of features to enhance the user's experience and increase the accessibility of the documents.

Technologies used in this project
* Streamlit
* AWS S3
* Apache Airflow
* Docker
* Google Cloud Platform
* FastAPI
* Great Expectations

## Implementation
![deployment_architecture_diagram](https://user-images.githubusercontent.com/108916132/235260615-d93723bb-91ca-4f2e-b723-427f6b53d6f0.png)

1. Built an end-to-end data pipeline to extract and preprocess PDF files using ‘Springer Nature’ publisher’s API and transfer to our AWS S3 bucket
2. Automated the process of ‘Springer Nature’ metadata scraping through Apache Airflow DAG which is scheduled on a daily basis
3. Designed and implemented RESTful APIs using FastAPI, to expose backend functionalities of the application to end-users
4. Secured the application endpoints by implementing Oauth2 JWT authentication and password hashing techniques
5. Developed a Streamlit web application that allows users to download the required PDF documents
6. Used Model as a Service (MaaS) approach to provide intelligent features such as translation, document recommendation, summarization, and querying the document itself.
    * Translation: using 'Google Translator API' to reproduce translated PDF
    * Recommendation: storing text embeddings of documents in Pinecone vector db and performing similarity match
    * Summarization: using Langchain and 'text-davinci-003' LLM from OpenAI
    * Doc query: using Langchain, Pinecone vector embeddings, and 'gpt-3.5-turbo'LLM from OpenAI
7. Containerized both Streamlit and FastAPI using 2 Docker containers, allowing for easier sharing and scalability. Published the Docker images on DockerHub, making it easily accessible to others over the internet (https://hub.docker.com/r/mittal15/streamlit_researchub/tags, https://hub.docker.com/r/mittal15/fastapi_researchub/tags)
8. Administered GitHub CI pipeline to automatically test code changes and streamline the development process
9. Deployed the application on a Google Cloud Platform (GCP) VM instance through a docker compose file, utilizing top-tier cloud computing infrastructure to provide fast and reliable hosting

## Files
```
📦 ResearcHub
.github
│  └─ workflows
│     └─ fastapi.yml
├─ .gitignore
README.md
airflow
│  └─ app
│     └─ dags
│        ├─ delete_files_dag.py
│        └─ researchub_dag.py
├─ docker-compose.yml
├─ fastapi
│  ├─ Dockerfile
│  ├─ base_model.py
│  ├─ basic_func.py
│  ├─ main.py
│  ├─ requirements.txt
│  └─ test_main.py
├─ great_expectations
│  ├─ .gitignore
│  ├─ checkpoints
│  │  ├─ first_checkpoint.yml
│  │  └─ run_first_checkpoint.py
│  ├─ expectations
│  │  └─ .ge_store_backend_id
│  ├─ greatExpectations.py
│  ├─ great_expectations.yml
│  ├─ plugins
│  │  └─ custom_data_docs
│  │     └─ styles
│  │        └─ data_docs_custom_styles.css
│  └─ run_first_checkpoint.py
└─ streamlit
   ├─ Dockerfile
   ├─ Home.py
   ├─ pages
   │  ├─ Edit_details.py
   │  ├─ Login.py
   │  ├─ Sign_up.py
   │  ├─ dashboard.py
   │  └─ main.py
   └─ requirements.txt
```

## Installation
To clone and replicate the project, please follow the steps below:

1. Open the command line interface (CLI) on your computer.
2. Navigate to the directory where you want to clone the repository.
3. Type `git clone https://github.com/Hmittal15/ResearcHub.git` and press Enter. This will clone the repository to your local machine.
4. Navigate into the cloned repository using `cd your-repo`
5. Set environment variables as mentioned below.
6. Create an AWS S3 bucket called `researchub` which should contain the `documents` folder and `researchub.db` file.
7. Install Airflow and run the DAGs on port 8080.
8. Pull the docker images from DockerHub using commands- `docker pull mittal15/fastapi_researchub:v1.0` and `docker pull mittal15/streamlit_researchub:v1.0`
9. Fire up the dockers using command `docker compose up` from project root directory. Streamlit app should be running on port 8000 and FastAPI should be running on port 8090. Happy browsing!

## Environment variables:
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

### Application demo:-


### Link to full explanatory video:-


## Application public link:
http://35.227.30.78:8000/

## Airflow DAGs:
http://35.227.30.78:8080/

## FastAPI docs:
http://35.227.30.78:8090/docs

## Technical document:
https://docs.google.com/document/d/1x2t97C4CWh-E8Rtmr6kRJsD-Z9fOeIUbViS4uFyuUvA/edit?usp=sharing

## You can find me on <a href="http://www.linkedin.com/in/harshit-mittal-52b292131"> <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/LinkedIn_logo_initials.png/768px-LinkedIn_logo_initials.png" width="17" height="17" /></a>