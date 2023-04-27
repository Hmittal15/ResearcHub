from langchain.document_loaders import OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.llms import OpenAI
import os
import sqlite3
from dotenv import load_dotenv
import boto3
import pandas as pd
from sqlalchemy import create_engine

load_dotenv()

s3client = boto3.client('s3', 
                        region_name='us-east-1',
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY')
                        )

user_bucket = os.environ.get('USER_BUCKET_NAME')

user_doc_title = "Carbon Fiber-Reinforced Polyurethane Composites with Modified Carbon–Polymer Interface"
summary=''

table_name="springer_metadata"
db_name="researchub.db"
db_engine=create_engine("sqlite:///" + db_name)

s3client.download_file(user_bucket, db_name, db_name)
df = pd.read_sql_table(table_name, con=db_engine)

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

print(summary)
os.remove(db_name)