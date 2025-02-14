from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import re
import faiss
from langchain.chains.question_answering import load_qa_chain
from langchain_openai.llms import OpenAI
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

index = faiss.read_index("faiss_index.index")
with open("faiss_metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

all_docs = metadata["documents"]
index_to_docstore_id = {i: i for i in range(len(all_docs))}

# 임베딩 함수 로드
embedding_function = OpenAIEmbeddings()

# FAISS 벡터 스토어 초기화
vectorstore = FAISS(
    index=index,
    docstore=metadata["metadatas"],
    index_to_docstore_id=index_to_docstore_id,
    embedding_function=embedding_function
)

# QA 체인 로드
llm = OpenAI()
qa_chain = load_qa_chain(llm, chain_type="stuff")

chat_model = ChatOpenAI(
    model_name="gpt-3.5-turbo-1106",
    temperature=0.1,
)

initial_system_message = """You are a theologian who knows the Bible very well.
Please list at least 5 or 10 most appropriate bible verses about a question or situation.
And comment each verse. Please answer with the contents of the revised Bible in Korean.
Please list at least 5 bible verses!!!!
You answer questions or situations in Korean."""

comment_system_message = """You are a theologian who knows the Bible very well. 
Use the word of the question as it is and add an explanation after that. Write it down in Korean.
Please comment on each Bible and explain it to me. Please answer with in Korean"""

# 책 이름 축약형 매핑
book_abbreviations = {
    "창세기": "창", "출애굽기": "출", "레위기": "레", "민수기": "민", "신명기": "신", 
    "여호수아": "수", "사사기": "삿", "룻기": "룻", "사무엘상": "삼상", "사무엘하": "삼하", 
    "열왕기상": "왕상", "열왕기하": "왕하", "역대상": "대상", "역대하": "대하", "에스라": "스", 
    "느헤미야": "느", "에스더": "에", "욥기": "욥", "시편": "시", "잠언": "잠", "전도서": "전", 
    "아가": "아", "이사야": "사", "예레미야": "렘", "예레미야애가": "애", "에스겔": "겔", 
    "다니엘": "단", "호세아": "호", "요엘": "욜", "아모스": "암", "오바댜": "옵", "요나": "욘", 
    "미가": "미", "나훔": "나", "하박국": "합", "스바냐": "습", "학개": "학", "스가랴": "슥", 
    "말라기": "말", "마태복음": "마", "마가복음": "막", "누가복음": "눅", "요한복음": "요", 
    "사도행전": "행", "로마서": "롬", "고린도전서": "고전", "고린도후서": "고후", "갈라디아서": "갈", 
    "에베소서": "엡", "엡소서": "엡", "빌립보서": "빌", "골로새서": "골", "데살로니가전서": "살전", "데살로니가후서": "살후", 
    "디모데전서": "딤전", "디모데후서": "딤후", "디도서": "딛", "빌레몬서": "몬", "히브리서": "히", 
    "야고보서": "약", "베드로전서": "벧전", "베드로후서": "벧후", "요한일서": "요일", "요한이서": "요이", 
    "요한삼서": "요삼", "유다서": "유", "요한계시록": "계"
}

def extract_verses(response_text):
    # 응답 텍스트에서 성경 구절 추출 (간단한 정규 표현식 사용)
    verse_pattern = re.compile(r"([가-힣]+\s?\d+:\d+)")
    verses = verse_pattern.findall(response_text)
    return verses

def get_abbreviated_verse(verse):
    # 성경 구절을 축약형으로 변환
    for full_name, abbreviation in book_abbreviations.items():
        if full_name in verse:
            return verse.replace(full_name, abbreviation)
    return verse

def get_all_possible_formats(verse):
    # 성경 구절의 모든 가능한 형식을 반환
    abbreviated_verse = get_abbreviated_verse(verse)
    book, chapter_verse = abbreviated_verse.split()
    chapter, verse = chapter_verse.split(":")
    formats = [
        f"{book} {chapter}:{verse}",
        f"{book}{chapter}:{verse}",
        f"{book} {chapter}장 {verse}절",
        f"{book}{chapter}장 {verse}절"
    ]
    return formats

def extract_exact_verse(text, verse):
    # 텍스트에서 정확한 구절만 추출
    verse_pattern = re.compile(rf"{verse}(.*?)(?=\s?[가-힣]+\s?\d+:\d+|\Z)", re.DOTALL)
    match = verse_pattern.search(text)
    if match:
        return match.group(0).strip()
    return "해당 구절을 찾을 수 없습니다."

def get_original_text_from_pdf(verse, documents):
    # 모든 가능한 형식으로 구절 검색
    possible_formats = get_all_possible_formats(verse)
    for doc in documents:
        for formatted_verse in possible_formats:
            if formatted_verse in doc.page_content:
                return extract_exact_verse(doc.page_content, formatted_verse)
    return "해당 구절을 찾을 수 없습니다."

def answer_question_with_system_message(question, system_message):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": question},
    ]
    result = chat_model.invoke(messages)
    return result.content

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        question = data.get('input')

        # 1단계: 첫 번째 응답 생성
        initial_response = answer_question_with_system_message(question, initial_system_message)
        # print(f"Initial response: {initial_response}")

        # 2단계: 첫 번째 응답에서 구절 추출
        verses = extract_verses(initial_response)
        # print(f"Extracted verses: {verses}")

        # 3단계: 추출된 구절을 PDF에서 검색하여 원본 텍스트 가져오기
        final_response = []
        final_answer = []
        for verse in verses:
            original_text = get_original_text_from_pdf(verse, all_docs)
            final_response.append(f"{original_text}")
            # print(f"Original text for verse {verse}: {original_text}")

            # print("")
            comment = answer_question_with_system_message(final_response[-1], comment_system_message)
            final_answer.append(comment)
            # print(f"Comment for verse {verse}: {comment}")
            # print("")

        # 길이 동기화: final_answer 리스트가 final_response 리스트와 같은 길이를 가지도록 조정
        while len(final_answer) < len(final_response):
            final_answer.append("주석을 생성하는 중 오류가 발생했습니다.")

        # 구절과 주석을 결합하여 응답 형식 구성
        combined_response = []
        for i in range(len(final_response)):
            combined_response.append(f"{i+1}) {final_response[i]}\n--> {final_answer[i]}\n")

        return jsonify({
            'initial_response': initial_response,
            'response': '\n'.join(combined_response)
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)


