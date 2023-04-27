import hashlib
import os
import botocore
import time
import openai
import requests
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import base_model
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine, text
from langchain.chains.summarize import load_summarize_chain
from langchain.llms import OpenAI
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar
from PyPDF2 import PdfReader
from fpdf import FPDF
from PIL import Image
import pandas as pd
from dotenv import load_dotenv
import re
import boto3
from sqlalchemy import create_engine
import pinecone
from sentence_transformers import SentenceTransformer
from langchain.document_loaders import OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import sqlite3

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# create a SQLAlchemy engine to connect to the database
engine = create_engine('sqlite:///researchub.db', echo=True)

openai.api_key = os.getenv("OPENAI_ACCESS_KEY")

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "fa5296715ded673b98da4a16672646ca2184ef4634fdedfeebfad085615b1ddc"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 2

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

load_dotenv()
database_file_name = 'researchub.db'
final_df = 0


#Establish connection to client
s3client = boto3.client('s3', 
                        region_name='us-east-1',
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY')
                        )


#Establish connection to logs
clientlogs = boto3.client('logs', 
                        region_name = 'us-east-1',
                        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                        )



# # Checks if the passed file exists in the specified bucket
# def check_if_file_exists_in_s3_bucket(bucket_name, file_name):
#     try:
#         s3client.head_object(Bucket=bucket_name, Key=file_name)
#         return True

#     except botocore.exceptions.ClientError as e:
#         if e.response['Error']['Code'] == '404':
#             return False
#         else:
#             raise


#Generating logs with given message in cloudwatch
def write_logs_researchub(message : str, endpoint : str, username='user-test'):
    log_group_name = "researchub"
    log_stream_name = "endpoint-logs"

    # Write log event to log stream
    log_message = f"[{username}] [{endpoint}] {message}"
    clientlogs.put_log_events(
        logGroupName=log_group_name,
        logStreamName=log_stream_name,
        logEvents=[
            {
                'timestamp': int(time.time() * 1e3),
                'message': log_message
            }
        ]
    )
    


# Copies the specified file from source bucket to destination bucket 
def copy_to_public_bucket(src_bucket_name, src_object_key, dest_bucket_name, dest_object_key):
    copy_source = {
        'Bucket': src_bucket_name,
        'Key': src_object_key
    }
    s3client.copy_object(Bucket=dest_bucket_name, CopySource=copy_source, Key=dest_object_key)


def get_users_data():
    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'researchub.db'))

    cursor = db.cursor()
    cursor.execute('''select * from users''')

    # Fetch all the rows as a list of tuples
    rows = cursor.fetchall()

    # Convert the rows to a list of dictionaries
    data = []
    for row in rows:
        # Create a dictionary with keys corresponding to the table column names
        record = {
            "username": row[0],
            "full_name": row[1],
            "email": row[2],
            "password": row[3]
        }
        data.append(record)
    return data


def verify_password(hashed_password, plain_password):
    return pwd_context.verify(plain_password, hashed_password)


def bcrypt(password: str):
        return pwd_context.hash(password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    my_dict={}
    for i in range(len(db)):
        if (db[i]['username']==username):
            data=get_users_data()
            my_dict=data[i]
    if my_dict:
        return base_model.UserInDB(**my_dict)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = base_model.TokenData(username=username)
    except JWTError:
        raise credentials_exception


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)


async def get_current_active_user(current_user: base_model.User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def add_user(username, password, email, full_name, plan, role):
    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'researchub.db'))

    cursor = db.cursor()
    
    # Hashing the password
    password_hash = pwd_context.hash(password)

    # call_count=0

    if "free" in plan:
        call_count = 10
    elif "gold" in plan:
        call_count = 15
    elif "platinum" in plan:
        call_count = 20

    # Inserting the details into users table
    cursor.execute("INSERT INTO users (username, fullname, password, email, plan, call_count, role) VALUES (?, ?, ?, ?, ?, ?, ?)", 
            (username, full_name, password_hash, email, plan, call_count, role))
    
    db.commit()

    db.close()

    s3client.upload_file(os.path.join(os.path.dirname(__file__), 'researchub.db'), 'researchub', 'researchub.db')

    return(f"User {username} created successfully with name {full_name} and subscription tier {plan}.")

# Define function to check if user already exists in database
def check_user_exists(username):
    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'researchub.db'))
    
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    result = cursor.fetchone()

    db.close()

    if bool(result):
        return False
    else:
        return True


# Gather all the appropriate options to be listed in the selection box
def list_filters(doc_type, subject, language, sort, author_name, keyword):


    # create a connection and a transaction
    with engine.connect() as conn:
        create_table = text('CREATE TEMPORARY TABLE temp_type AS SELECT * FROM springer_metadata;')
        conn.execute(create_table)
        
        select_table = text('SELECT DISTINCT TYPE FROM temp_type;')
        distinct_types = [row[0] for row in conn.execute(select_table)]

        hyphen = "-"

        if hyphen not in distinct_types:
            distinct_types.insert(0, hyphen)

        if doc_type == "-":
            conn.execute(text('CREATE TEMPORARY TABLE temp_subj AS SELECT * FROM temp_type;'))

        else:
            conn.execute(text(f'CREATE TEMPORARY TABLE temp_subj AS SELECT * FROM temp_type WHERE TYPE = "{doc_type}";'))

            
        distinct_subjs = [row[0] for row in conn.execute(text('SELECT DISTINCT CATEGORY FROM temp_subj;'))]

        if hyphen not in distinct_subjs:
            distinct_subjs.insert(0, hyphen)


        if subject =="-":
            conn.execute(text('CREATE TEMPORARY TABLE temp_lang AS SELECT * FROM temp_subj;'))

        else:

            conn.execute(text(f'CREATE TEMPORARY TABLE temp_lang AS SELECT * FROM temp_subj WHERE  CATEGORY = "{subject}";'))


        distinct_langs = [row[0] for row in conn.execute(text('SELECT DISTINCT LANGUAGE FROM temp_lang;'))]

        if hyphen not in distinct_langs:
            distinct_langs.insert(0, hyphen)

        
        if(language == "-"):
            conn.execute(text('CREATE TEMPORARY TABLE temp_auth AS SELECT * FROM temp_lang;'))
        else:
            conn.execute(text(f'CREATE TEMPORARY TABLE temp_auth AS SELECT * FROM temp_lang WHERE LANGUAGE = "{language}";'))

        
        if(author_name == ""):
            conn.execute(text('CREATE TEMPORARY TABLE temp_keyword AS SELECT * FROM temp_auth;'))

        else:
            conn.execute(text(f'CREATE TEMPORARY TABLE temp_keyword AS SELECT * FROM temp_auth WHERE AUTHORS LIKE "%{author_name}%";'))


        if(keyword == ""):
            conn.execute(text('CREATE TEMPORARY TABLE temp_docs AS SELECT * FROM temp_keyword;'))

        else:
            conn.execute(text(f'CREATE TEMPORARY TABLE temp_docs AS SELECT * FROM temp_keyword WHERE KEYWORDS LIKE "%{keyword}%";'))


        query = conn.execute(text('SELECT TITLE FROM temp_docs;'))


        docs_list = [row[0] for row in query]
       

        if 'Oldest First' in sort :
            query = conn.execute(text('SELECT TITLE FROM temp_docs ORDER BY DATE;'))
            docs_list = [row[0] for row in query]
        elif 'Latest First' in sort:
            query = conn.execute(text('SELECT TITLE FROM temp_docs ORDER BY DATE DESC;'))
            docs_list = [row[0] for row in query]
        
        # conn.execute(text('DROP TABLE temp_docs, temp_keyword, temp_auth, temp_lang, temp_subj, temp_type;'))
        tables = ['temp_docs', 'temp_keyword', 'temp_auth', 'temp_lang', 'temp_subj', 'temp_type']

        for table in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS {table};"))

    return {"distinct_types" : distinct_types, "distinct_subjs" : distinct_subjs, "distinct_langs" : distinct_langs, "docs_list" : docs_list }



# Retrieving the log events for a given username
def get_endpoint_count_for_username(endpoint = 'any', username = 'admin', duration = 'none'):
    # Declare timeframe based on the given duration
    if duration == 'hour':
        timeframe = 1
    elif duration == 'day':
        timeframe = 24
    elif duration == 'week':
        timeframe = 24*7
    elif duration == 'month':
        timeframe = 24*30
    

    # Define the start and end times for the query
    end_time = int(time.time() * 1000)
    if duration != 'none':
        start_time = end_time - (timeframe * 60 * 60 * 1000) 
    else:
        start_time = 0

    # Query logs to get the number of calls made
    if username == 'admin':
        query = f"fields @timestamp, @message | stats count()"
        if endpoint == 'any':
            query = f"fields @timestamp, @message | stats count()"
        else:
            query = f"fields @timestamp, @message | stats count() | filter @message like /{endpoint}/"
    else:
        if endpoint == 'any':
            query = f"fields @timestamp, @message | stats count() | filter @message like /{username}/"
        else:
            query = f"fields @timestamp, @message | stats count() | filter @message like /{endpoint}/ and @message like /{username}/"
    

    response = clientlogs.start_query(
        logGroupName='researchub',
        startTime=start_time,
        endTime=end_time,
        queryString=query,
        limit=10000
    )

    # Get the query id to check status
    query_id = response['queryId']
    status = None

    # Wait till the query is completed
    while status == None or status == 'Running':
        status = clientlogs.get_query_results(
            queryId=query_id
        )['status']
        time.sleep(1)

    # Get the result of the query
    results = clientlogs.get_query_results(queryId=query_id)['results']

    # print(results[0][0]['value'])

    # Return the result if retrieved or return 0
    if len(results) > 0:
        endpoint_count = int(results[0][0]['value'])
        return endpoint_count
    else:
        return 0
    

# Check whether user has calls
def download_document(selected_doc : str, username : str):
    try:
        with engine.connect() as conn:
            query = conn.execute(text(f"SELECT DISTINCT DOC_URL FROM springer_metadata where TITLE = '{selected_doc}';"))
            selected_url = [row[0] for row in query]
        # print(selected_url)

        response = requests.get(selected_url[0])
        filename = f'{selected_doc}.pdf'
        with open(filename, 'wb') as f:
            f.write(response.content)
        print (filename)

        # Upload the file to S3

        bucket_name = 'researchub'
        key = f'documents/{filename}'
        s3client.upload_file(filename, bucket_name, key)

        # Delete the local file
        os.remove(filename)

        # Generates the download URL of the specified file present in the given bucket and write logs in S3
        
        response = s3client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket_name,
                'Key': key
            },
            ExpiresIn=3600        
        )

        # print(response)

        write_logs_researchub(f'Requested download link for {selected_doc}', 'download-url', username)

        return response
    except:
        return "fail"
    

def generate_summary(user_doc_title, username):
    try:
        # user_doc_title = f'documents/{user_doc_title}.pdf'
        user_bucket = os.environ.get('USER_BUCKET_NAME')
        db_name="researchub.db"
        table_name="springer_metadata"

        s3client.download_file(user_bucket, db_name, db_name)
        df = pd.read_sql_table(table_name, con=engine)

        for index, row in df.iterrows():
            # print(row['url'])
            if (row['TITLE'] == user_doc_title):
                loader = OnlinePDFLoader(row['DOC_URL'])

                data = loader.load()

                # print (f'We have {len(data)} document(s) in our data')
                # print (f'There are {len(data[0].page_content)} characters in our document')

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
                texts = text_splitter.split_documents(data)

                # restricting passing of long data to summarization model
                # limiting ot only first 25k characters
                if (len(texts)>25):
                    texts=texts[:25]

                # print (f'Now we have {len(texts)} documents')

                llm = OpenAI(model_name="text-davinci-003", openai_api_key=os.getenv("OPENAI_ACCESS_KEY"))

                chain = load_summarize_chain(llm, chain_type="map_reduce")
                summary = chain.run(texts)
        
        write_logs_researchub(f'Requested the summary of the document "{user_doc_title}"', 'summary-generation', username)

        return(summary)
    except:
        return "fail"


def add_text_images(text_list, my_size, my_font, my_page, is_last_record, pdf):
    # print(text_list)
    # print(my_size)
    # print(my_font)
    # print(my_page)

    image_list=[]
    if os.path.exists("images"):
        # Loop through all files in the directory
        for filename in os.listdir("images"):
            if filename.endswith(".png"):
                image_list.append(filename)  # Add the full path of the image file to the list
        page_list=[]
        for file in image_list:
            page_list.append(file.split("_")[0])

    if (pdf.page_no()<my_page+1):
        pdf.add_page()
    
    pdf.set_font(my_font, size=my_size)
    for text in text_list:
        # Replace problematic characters with a replacement character
        text = text.encode('latin-1', errors='replace').decode('latin-1')

        # Split the text into multiple lines
        lines = text.split('\n')

        # Output each line using MultiCell
        for line in lines:
            pdf.multi_cell(0, 5, line)

    if (is_last_record):
        if os.path.exists("images"):
            for image_page in page_list:
                # Add a blank line
                pdf.cell(5, 10, '')
                if (int(image_page) == pdf.page_no()):
                    # Get the current cursor position
                    current_y = pdf.get_y()

                    for image_file in image_list:
                        if ( image_file.split("_")[0] == image_page):
                            my_filename = "images/" + image_file
                            img = Image.open(my_filename)
                            width, height = img.size
                            if width > height:
                                ratio = 100 / width
                            else:
                                ratio = 190 / height
                            width *= ratio
                            height *= ratio
                            pdf.image(my_filename, x=10, y=current_y, w=width, h=height)
                            
                            # Add a blank line
                            pdf.cell(5, 10, '')

                            image_list.remove(image_file)

                    # Add a blank line
                    pdf.cell(5, 10, '')


def google_translate_text(target, text, current_font, current_size, current_page, is_last_record, pdf):

    url = "https://google-translator9.p.rapidapi.com/v2"

    payload = {
        "q": text,
        "target": target,
        "source": "en",
        "format": "text"
    }

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": os.environ.get('RAPID_API_KEY'),
        "X-RapidAPI-Host": os.environ.get('RAPID_API_HOST')
    }

    response = requests.request("POST", url, json=payload, headers=headers).json()

    add_text_images([response["data"]["translations"][0]["translatedText"]], current_size, current_font, current_page, is_last_record, pdf)


def text_processing(Extract_Font, Extract_Size, Extract_Data, Extract_page, pdf, translate_to):

    for i in range(len(Extract_Font)):
        if ("Times" in Extract_Font[i]):
            Extract_Font[i]='Times'
        elif ("Zap" in Extract_Font[i]):
            Extract_Font[i]='ZapfDingbats'
        elif ("Courier" in Extract_Font[i]):
            Extract_Font[i]='Courier'
        elif ("Helvetica" in Extract_Font[i]):
            Extract_Font[i]='Helvetica'
        elif ("Arial" in Extract_Font[i]):
            Extract_Font[i]='Arial'
        elif ("Symbol" in Extract_Font[i]):
            Extract_Font[i]='Symbol'
        else:
            Extract_Font[i]='Times'

    i=0
    current_size=Extract_Size[0]
    current_font=Extract_Font[0]
    current_data=""
    current_page=Extract_page[0]

    while i<len(Extract_Size):
        current_size=Extract_Size[i]
        current_font=Extract_Font[i]
        current_data=Extract_Data[i]
        current_page=Extract_page[i]

        c=1
        for j in range(i+1, len(Extract_Size)):
            if (( current_size == Extract_Size[j] ) and ( current_font == Extract_Font[j] ) and ( current_page == Extract_page[j] )):
                current_data = current_data + Extract_Data[j]
                c+=1
            elif (current_page != Extract_page[j]):
                google_translate_text(translate_to, current_data, current_font, current_size, current_page, True, pdf)
                current_data=""
                break
            else:
                google_translate_text(translate_to, current_data, current_font, current_size, current_page, False, pdf)
                current_data=""
                break
        i=i+c
    
    if (current_data!=""):
        google_translate_text(translate_to, current_data, current_font, current_size, current_page, True, pdf)


def extract_images(path, Extract_Font, Extract_Size, Extract_Data, Extract_page, pdf, translate_to):
    with open(path,"rb") as f:
        reader = PdfReader(f)

        has_images = False
        for page in reader.pages:
            if page.images:
                has_images = True
                break
        if has_images:
            # print("The PDF contains at least one image.")

            if not os.path.exists("images"):
                os.makedirs("images")

            for page_num in range(0,len(reader.pages)):
                selected_page = reader.pages[page_num]
                for i, img_file_obj in enumerate(selected_page.images):
                    with open('images/'+str(page_num+1)+"_image_"+str(i)+".png", "wb") as out:
                        out.write(img_file_obj.data)

    text_processing(Extract_Font, Extract_Size, Extract_Data, Extract_page, pdf, translate_to)


def extract_text(path, pdf, translate_to):
    Extract_Font=[]
    Extract_Size=[]
    Extract_Data=[]
    Extract_page=[]

    for i, page_layout in enumerate(extract_pages(path)):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    try:
                        for character in text_line:
                            if isinstance(character, LTChar):
                                Font_size=character.size
                                Font_style=character.fontname
                    except:
                        pass
                Extract_Font.append(Font_style)
                Extract_Size.append(int(Font_size))
                Extract_Data.append(element.get_text())
                Extract_page.append(i)
    # print(Extract_page)
    extract_images(path, Extract_Font, Extract_Size, Extract_Data, Extract_page, pdf, translate_to)


def generate_translation(filename, username, translate_to):
    # filename="documentation.pdf"
    try:
        user_bucket = os.environ.get('USER_BUCKET_NAME')

        with engine.connect() as conn:
            query = conn.execute(text(f"SELECT DISTINCT DOC_URL FROM springer_metadata where TITLE = '{filename}';"))
            selected_url = [row[0] for row in query]
        # print(selected_url)

        response = requests.get(selected_url[0])
        filename = f'{filename}.pdf'
        with open(filename, 'wb') as f:
            f.write(response.content)
        print (filename)

        # Upload the file to S3

        bucket_name = 'researchub'
        key = f'documents/{filename}'
        s3client.upload_file(filename, bucket_name, key)

        # Delete the local file
        os.remove(filename)

        # filename_key = f'documents/{filename}.pdf'
        # Download the file from S3
        s3client.download_file(user_bucket, key, filename)

        pdf = FPDF()
        pdf.add_page()

        extract_text(filename, pdf, translate_to)

        pdf.output(filename.split(".")[0]+"_translated.pdf")

        file_key = f'documents/{filename.split(".")[0]}_translated.pdf'

        # Upload the file to S3
        with open(filename.split(".")[0]+"_translated.pdf", 'rb') as f:
            s3client.upload_fileobj(f, user_bucket, file_key)

        os.remove(filename)
        os.remove(filename.split(".")[0]+"_translated.pdf")

        # Delete the images directory and all its contents
        if os.path.exists("images"):
            for filename in os.listdir("images"):
                file_path = os.path.join("images", filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)

            os.rmdir("images")

        # Generates the download URL of the specified file present in the given bucket and write logs in S3
        
        response = s3client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket_name,
                'Key': file_key
            },
            ExpiresIn=3600        
        )

        write_logs_researchub(f'Requested translation for the document {filename}', 'translation-generation', username)
        return response
    
    except:
        # Delete the images directory and all its contents
        if os.path.exists("images"):
            for filename in os.listdir("images"):
                file_path = os.path.join("images", filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)

            os.rmdir("images")
        return "fail"


# One-time process to create an index initially
def initialize_vector_db():
    pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv('PINECONE_ENV'))
    index_name="doc-recommend"

    # If index of the same name exists, then delete it
    if index_name in pinecone.list_indexes():
        pinecone.delete_index(index_name)

    pinecone.create_index(index_name, dimension=384, metric="cosine", pods=1, pod_type="p1.x1")


def generate_recommendation(user_doc_title, username):
    try:
        user_bucket = os.environ.get('USER_BUCKET_NAME')

        # user_doc_title="Tactile perception of textile fabrics based on friction and brain activation"
        user_doc_abstract=''
        user_doc_keywords=''
        table_name="springer_metadata"
        db_name="researchub.db"

        s3client.download_file(user_bucket, db_name, db_name)
        user_df = pd.read_sql_table(table_name, con=engine)
        for i, row in user_df.iterrows():
            if (row['TITLE']==user_doc_title):
                # user_doc_summary = row['SUMMARY']
                user_doc_abstract = row['ABSTRACT']
                user_doc_keywords = row['KEYWORDS']
                user_doc_url = row['DOC_URL']

        df=pd.DataFrame(columns=['Document title', 'Match percentage'])
        titles=[]
        percentage=[]

        model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

        pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv('PINECONE_ENV'))
        index_name="doc-recommend"
        index = pinecone.Index(index_name)

        loader = OnlinePDFLoader(user_doc_url)
        data = loader.load()

        xq = model.encode(str(data) + "Following is the abstract for this document. " + user_doc_abstract + "Following are the crucial keywords which are described in this document. " + user_doc_keywords).tolist()
        result = index.query(xq, top_k=6, include_metadata=True)

        for i in range(len(result['matches'])):
            if (user_doc_title != result['matches'][i]['metadata']['title']):
                titles.append(result['matches'][i]['metadata']['title'])
                percentage.append(int(result['matches'][i]['score'] * 100))

        
        df['Document title']=titles
        df['Match percentage']=percentage


        write_logs_researchub(f'Requested recommendations for the document "{user_doc_title}"', 'recommendation-generation', username)

        return df.to_dict()
    except:
        return "fail"

# One-time process to create an index initially
def initialize_doc_query_vector():
    pinecone.init(api_key=os.getenv('PINECONE_API_KEY_DOC'), environment=os.getenv('PINECONE_ENV_DOC'))
    index_name="doc-query"

    # If index of the same name exists, then delete it
    if index_name in pinecone.list_indexes():
        pinecone.delete_index(index_name)

    pinecone.create_index(index_name, dimension=384, metric="cosine", pods=1, pod_type="p1.x1")


def vector_encoding_smart_doc(user_doc_title):

    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    user_bucket = os.environ.get('USER_BUCKET_NAME')

    table_name="springer_metadata"
    db_name="researchub.db"

    s3client.download_file(user_bucket, db_name, db_name)
    df = pd.read_sql_table(table_name, con=engine)

    texts=[]

    try:
        for index, row in df.iterrows():
            # print(row['url'])
            if (row['TITLE'] == user_doc_title):
                print(user_doc_title)
                loader = OnlinePDFLoader(row['DOC_URL'])
                data = loader.load()

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=20)
                texts = text_splitter.split_documents(data)
        
        pinecone.init(api_key=os.getenv('PINECONE_API_KEY_DOC'), environment=os.getenv('PINECONE_ENV_DOC'))
        index_name="doc-query"
        index = pinecone.Index(index_name)

        embedding_list = []
        for i in range(len(texts)):
            embedding_list.append((
                str(i),
                model.encode(str(texts[i])).tolist(),
                {'context': str(texts[i])}
            ))
        # if len(embedding_list)==50 or len(embedding_list)==len(df):
            index.upsert(vectors=embedding_list)
            embedding_list = []

    except:
        return False
    

def doc_query(query, username):
    try:
        openai.api_key = os.environ.get("OPENAI_ACCESS_KEY")

        model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

        pinecone.init(api_key=os.getenv('PINECONE_API_KEY_DOC'), environment=os.getenv('PINECONE_ENV_DOC'))
        index_name="doc-query"
        index = pinecone.Index(index_name)

        query_doc = model.encode(query).tolist()
        result = index.query(query_doc, top_k=1, include_metadata=True)

        print(result)
        print(query)

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "As a professor, answer below question using the provided context only. If information is insufficient, respond saying Information not available in the document. Context: " + result['matches'][0]['metadata']['context'] + '\n\n' + "Question: " + query}
            ]
        )

        write_logs_researchub(f'Queried using smart-doc. Query : {query}', 'doc-query-smart-doc', username)
        return (completion.choices[0].message["content"])
    except:
        return "fail"

def check_if_title_exists(smart_doc_name):

    with engine.connect() as conn:
        query = conn.execute(text(f'SELECT TITLE FROM springer_metadata where title = "{smart_doc_name}";'))
        titles = [row[0] for row in query]
    
    if len(titles) > 0:
        return True
    else:
        return False

def check_users_api_record(userid: str):

    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))

    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'researchub.db'))
    
    cursor = db.cursor()
    
    select_q_users = f'select plan from users where username="{userid}"'
    cursor.execute(select_q_users)
    result_plan = cursor.fetchone()

    user_plan = ""
    max_limit = 0
    if ("free" in result_plan):
        user_plan="free"
        max_limit=10
    if ("gold" in result_plan):
        user_plan="gold"
        max_limit=15
    if ("platinum" in result_plan):
        user_plan="platinum"
        max_limit=20
    
    select_q = f'select * from users_api_record where username="{userid}"'
    cursor.execute(select_q)
    result = cursor.fetchall()
        
    if (result!=[]):
        update_q_user_total_count = f'UPDATE users_api_record SET max_count = {max_limit}, plan = "{user_plan}" WHERE username="{userid}"'
        cursor.execute(update_q_user_total_count)
        cursor.execute(select_q)
        updated_result = cursor.fetchall()

        now = datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        timedelta = now - datetime.strptime(result[0][1], '%Y-%m-%d %H:%M:%S')

        if ((updated_result[0][4] >= updated_result[0][3]) and (timedelta.total_seconds() < 60 * 60)):
            return False
    
    db.commit()
    db.close()

    s3client.upload_file(os.path.join(os.path.dirname(__file__), 'researchub.db'), 'researchub', 'researchub.db')

    return True


def update_users_api_record(endpoint: str, response_status: str, userid: str):

    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))

    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'researchub.db'))
    
    cursor = db.cursor()
    
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    update_col = ""
    if ("/download-url" in endpoint):
        update_col = "doc_download"
    elif ("/summary-generation" in endpoint):
        update_col = "summary_generation"
    elif ("/translation-generation" in endpoint):
        update_col = "translation_generation"
    elif ("/recommendation-generation" in endpoint):
        update_col = "recommendation_generation"
    elif ("/doc-query-smart-doc" in endpoint):
        update_col = "smart_doc"
    
    select_q_users = f'select plan from users where username="{userid}"'
    cursor.execute(select_q_users)
    result_plan = cursor.fetchone()

    user_plan = ""
    max_limit = 0
    if ("free" in result_plan):
        user_plan="free"
        max_limit=10
    if ("gold" in result_plan):
        user_plan="gold"
        max_limit=15
    if ("platinum" in result_plan):
        user_plan="platinum"
        max_limit=20
    
    if ("fail" in response_status):
        update_q = f'UPDATE users_api_record SET {update_col} = ((select {update_col} from users_api_record where username="{userid}") + 1), failure = ((select failure from users_api_record where username="{userid}") + 1) WHERE username="{userid}"'
    else:
        update_q = f'UPDATE users_api_record SET {update_col} = ((select {update_col} from users_api_record where username="{userid}") + 1), success = ((select success from users_api_record where username="{userid}") + 1) WHERE username="{userid}"'
        
    select_q = f'select * from users_api_record where username="{userid}"'
    insert_q_user_api = f'insert into users_api_record (username, first_call, plan, max_count, total_count, doc_download, summary_generation, translation_generation, recommendation_generation, smart_doc, success, failure) values ("{userid}", "{now_str}", "{user_plan}", {max_limit}, 1, 0, 0, 0, 0, 0, 0, 0)'
    update_q_user_total_count = f'UPDATE users_api_record SET total_count = ((select total_count from users_api_record where username="{userid}") + 1) WHERE username="{userid}"'
    delete_q_user_api = f'delete from users_api_record where username = "{userid}"'
    
    cursor.execute(select_q)
    result = cursor.fetchall()
    
    if result!=[]:
        timedelta = now - datetime.strptime(result[0][1], '%Y-%m-%d %H:%M:%S')
        insert_q_app_api = f'insert into app_api_record (username, first_call, plan, max_count, total_count, doc_download, summary_generation, translation_generation, recommendation_generation, smart_doc, success, failure) values {result[0]}'
    
    if result==[]:
        cursor.execute(insert_q_user_api)
        cursor.execute(update_q)

    elif ((result!=[]) and (timedelta.total_seconds() < 60 * 60)):
        if (result[0][4] < result[0][3]):
            cursor.execute(update_q)
            cursor.execute(update_q_user_total_count)
        else:
            return False
    
    elif ((result!=[]) and (timedelta.total_seconds() >= 60 * 60)):
        cursor.execute(insert_q_app_api)
        cursor.execute(delete_q_user_api)
        cursor.execute(insert_q_user_api)
        cursor.execute(update_q)
        
    
    db.commit()
    db.close()
   
    s3client.upload_file(os.path.join(os.path.dirname(__file__), 'researchub.db'), 'researchub', 'researchub.db')
    
    return True

# Define function to update password in database
def update_password(username, password):

    # Hashing the password
    password_hash = pwd_context.hash(password)

    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'users.db'))
    c = db.cursor()

    c.execute("UPDATE users SET password=? WHERE username=?", (password_hash, username))

    db.commit()

    db.close()

    s3client.upload_file(os.path.join(os.path.dirname(__file__), 'researchub.db'), 'researchub', 'researchub.db')


# Define function to update password in database
def update_plan(username, new_plan):

    # Connect to database
    s3client.download_file('researchub', 'researchub.db', os.path.join(os.path.dirname(__file__), 'researchub.db'))
    db = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'researchub.db'))
    c = db.cursor()

    if "free" in new_plan:
        call_count = 10
    elif "gold" in new_plan:
        call_count = 15
    elif "platinum" in new_plan:
        call_count = 20

    c.execute("UPDATE users SET plan=?, call_count=? WHERE username=?", (new_plan, call_count, username))

    db.commit()

    db.close()

    s3client.upload_file(os.path.join(os.path.dirname(__file__), 'researchub.db'), 'researchub', 'researchub.db')