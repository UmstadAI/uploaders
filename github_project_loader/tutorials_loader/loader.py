import glob
import os
import openai
import pinecone
import time

from uuid import uuid4
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter, Language

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv(), override=True) # read local .env file

openai.api_key = os.getenv('OPENAI_API_KEY') or 'OPENAI_API_KEY'
pinecone_api_key = os.getenv('PINECONE_API_KEY') or 'YOUR_API_KEY'
pinecone_env = os.getenv('PINECONE_ENVIRONMENT') or "YOUR_ENV"

path_tutorial_docs = "../../doc_loader/files/docs2/zkapps/tutorials"

files = os.listdir(path_tutorial_docs)

md_files = [file for file in os.listdir(path_tutorial_docs) if file.endswith(".md")]
docs = DirectoryLoader(path_tutorial_docs + "/", glob="**/*.md", loader_cls=TextLoader, show_progress=True).load()

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
md_header_splitted_docs = [markdown_splitter.split_text(doc.page_content) for doc in docs]

# Char-level splits
from langchain.text_splitter import RecursiveCharacterTextSplitter

# SPLITTING
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=200
)

splitted_docs = [text_splitter.split_documents(doc) for doc in md_header_splitted_docs]

#EMBEDDING
model_name = 'text-embedding-ada-002'
texts = [t.page_content for c in splitted_docs for t in c]

print("Created", len(texts), "texts")

chunks = [texts[i:(i + 1000) if (i+1000) <  len(texts) else len(texts)] for i in range(0, len(texts), 1000)]
embeds = []

metadatas = [t.metadata for c in splitted_docs for t in c]
print("Metadatas length: ", len(metadatas))

print("Have", len(chunks), "chunks")
print("Last chunk has", len(chunks[-1]), "texts")

for chunk, i in zip(chunks, range(len(chunks))):
    print("Chunk", i, "of", len(chunk))
    new_embeddings = openai.Embedding.create(
        input=chunk,
        model=model_name,
    )
    new_embeds = [record['embedding'] for record in new_embeddings['data']]
    embeds.extend(new_embeds)

print("Embeds length: ", len(embeds))

pinecone.init(api_key=pinecone_api_key, environment=pinecone_env)

index_name = 'zkappumstad'

ids = [str(uuid4()) for _ in range(len(texts))]

vectors = [(ids[i], embeds[i], {
    "content": texts[i],
    "metadata": metadatas[i]
}) for i in range(len(texts))]

print(vectors[35])



