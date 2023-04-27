import pandas as pd
from dotenv import load_dotenv
import os
import pinecone
from sentence_transformers import SentenceTransformer
import re
import boto3
from sqlalchemy import create_engine
import os
import pinecone
from sentence_transformers import SentenceTransformer
from langchain.document_loaders import OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import openai

openai.api_key = os.getenv("OPENAI_ACCESS_KEY")

load_dotenv()

s3client = boto3.client('s3', 
                        region_name='us-east-1',
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY')
                        )

user_bucket = os.environ.get('USER_BUCKET_NAME')

def doc_query(query):
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    pinecone.init(api_key=os.getenv('PINECONE_API_KEY_DOC'), environment=os.getenv('PINECONE_ENV_DOC'))
    index_name="doc-query"
    index = pinecone.Index(index_name)

    query_doc = model.encode(query).tolist()
    result = index.query(query_doc, top_k=1, include_metadata=True)

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "As a professor, answer below question using the provided context only. If information is insufficient, respond saying Information not available in the document. Context: " + result['matches'][0]['metadata']['context'] + '\n\n' + "Question: " + query}
        ]
    )
    print(completion.choices[0].message["content"])

def vector_encoding(user_doc_title):
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    table_name="springer_metadata"
    db_name="researchub.db"
    db_engine=create_engine("sqlite:///" + db_name)

    s3client.download_file(user_bucket, db_name, db_name)
    df = pd.read_sql_table(table_name, con=db_engine)

    texts=[]

    try:
        for index, row in df.iterrows():
            # print(row['url'])
            if (row['TITLE'] == user_doc_title):
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

        os.remove(db_name)

    except:
        return False

# One-time process to create an index initially
def initialize_doc_query_vector():
    pinecone.init(api_key=os.getenv('PINECONE_API_KEY_DOC'), environment=os.getenv('PINECONE_ENV_DOC'))
    index_name="doc-query"

    # If index of the same name exists, then delete it
    if index_name in pinecone.list_indexes():
        pinecone.delete_index(index_name)

    pinecone.create_index(index_name, dimension=384, metric="cosine", pods=1, pod_type="p1.x1")

if __name__=="__main__":
    vector_encoding("Low friction of superslippery and superlubricity: A review")
    doc_query("what day is today?")