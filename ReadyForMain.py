import glob
import pickle
import faiss
import numpy as np
from langchain_community.document_loaders import PyPDFLoader
from langchain.document_loaders import PyMuPDFLoader
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

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

# 문서와 메타데이터 저장
with open("faiss_metadata.pkl", "wb") as f:
    pickle.dump({"documents": all_docs, "metadatas": {i: doc for i, doc in enumerate(all_docs)}}, f)

print("FAISS 인덱스와 메타데이터를 저장했습니다.")



