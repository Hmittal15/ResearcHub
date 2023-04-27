import pandas as pd
from dotenv import load_dotenv
import boto3
from sqlalchemy import create_engine
import os
import pinecone
from sentence_transformers import SentenceTransformer
from langchain.document_loaders import OnlinePDFLoader
import re

load_dotenv()

s3client = boto3.client('s3', 
                        region_name='us-east-1',
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY')
                        )

user_bucket = os.environ.get('USER_BUCKET_NAME')

def vector_query():

    user_doc_title="Tactile perception of textile fabrics based on friction and brain activation"
    user_doc_abstract=''
    user_doc_keywords=''
    table_name="springer_metadata"
    db_name="researchub.db"
    db_engine=create_engine("sqlite:///" + db_name)

    s3client.download_file(user_bucket, db_name, db_name)
    user_df = pd.read_sql_table(table_name, con=db_engine)
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

    print(df)

    os.remove(db_name)

# This process will be automated through DAG to upsert new records in vector database on daily basis
def vector_encoding():
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    table_name="springer_metadata"
    db_name="researchub.db"
    db_engine=create_engine("sqlite:///" + db_name)

    s3client.download_file(user_bucket, db_name, db_name)
    df = pd.read_sql_table(table_name, con=db_engine)

    pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv('PINECONE_ENV'))
    index_name="doc-recommend"
    index = pinecone.Index(index_name)

    embedding_list = []
    for i, row in df.iterrows():
        loader = OnlinePDFLoader(row['DOC_URL'])
        data = loader.load()
        embedding_list.append((
            re.sub('[^A-Za-z0-9]+', '', row['TITLE']),
            model.encode(str(data) + "Following is the abstract for this document. " + row['ABSTRACT'] + "Following are the crucial keywords which are described in this document. " + row['KEYWORDS']).tolist(),
            {'title': row['TITLE']}
        ))
    # if len(embedding_list)==50 or len(embedding_list)==len(df):
        index.upsert(vectors=embedding_list)
        embedding_list = []

    os.remove(db_name)

# One-time process to create an index initially
def initialize_vector_db():
    pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv('PINECONE_ENV'))
    index_name="doc-recommend"

    # If index of the same name exists, then delete it
    if index_name in pinecone.list_indexes():
        pinecone.delete_index(index_name)

    pinecone.create_index(index_name, dimension=384, metric="cosine", pods=1, pod_type="p1.x1")

if __name__=="__main__":
    # initialize_vector_db()
    # vector_encoding()
    vector_query()