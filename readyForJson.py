# ------------------json파일로 변경-----------------

import glob
import json
import faiss
import numpy as np
from langchain_community.document_loaders import PyPDFLoader, PyMuPDFLoader
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Document 객체를 JSON 호환 형식으로 변환하는 함수
def document_to_dict(doc):
    return {
        'page_content': doc.page_content,
        'metadata': doc.metadata
    }

# PDF 파일이 있는 디렉토리 경로
pdf_directory = "bible/"

# 모든 PDF 파일 경로 가져오기
pdf_files = glob.glob(pdf_directory + "*.pdf")

# 모든 문서를 저장할 리스트
all_docs = []

# 모든 PDF 파일 로드 및 청크로 분할
for pdf_file in pdf_files:
    loader = PyMuPDFLoader(pdf_file)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    all_docs.extend(docs)

# 로드된 문서 수 확인
print(f"총 문서 수: {len(all_docs)}")

# 임베딩 생성
embeddings = OpenAIEmbeddings()
doc_texts = [doc.page_content for doc in all_docs]
doc_embeddings = embeddings.embed_documents(doc_texts)

# numpy 배열로 변환
doc_embeddings = np.array(doc_embeddings)

# FAISS 인덱스 생성
dimension = doc_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(doc_embeddings)

# FAISS 인덱스 저장
faiss.write_index(index, "faiss_index.index")

# 문서와 메타데이터 저장 (JSON 형식으로 변환)
documents_dict = [document_to_dict(doc) for doc in all_docs]
metadata = {"documents": documents_dict, "metadatas": {i: document_to_dict(doc) for i, doc in enumerate(all_docs)}}

# JSON 파일로 저장
output_path = "faiss_metadata.json"
with open(output_path, "w", encoding='utf-8') as f:
    json.dump(metadata, f, ensure_ascii=False, indent=4)

print("FAISS 인덱스와 메타데이터를 JSON 파일로 저장했습니다.")
