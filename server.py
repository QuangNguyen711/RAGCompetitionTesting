from pathlib import Path

import faiss
import numpy as np
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import pickle

# ================= CẤU HÌNH =================
SERVER_URL = "http://127.0.0.1:8000"  # IP Server Ban tổ chức
STUDENT_ID = "B21DCCN001"             # Mã sinh viên
LOCAL_PORT = 3636                     # Port chạy server của sinh viên 
LOCAL_MODEL_DIR = Path(__file__).resolve().parent / "models" / "vietnamese-sbert"
FAISS_PATH = "vector_db.faiss"
CHUNKS_PATH = "chunks.pkl"

# ================= BIẾN TOÀN CỤC =================
app = FastAPI()
embed_model = None
client = None
index = None
chunks = []

def chunk_text(text, chunk_size=500, overlap=50):
    # laws = text.split("###")
    # chunks_list = []
    # for law in laws:
    #     words = law.split()
    #     for i in range(0, len(words), chunk_size - overlap):
    #         chunk = " ".join(words[i : i + chunk_size])
    #         chunks_list.append(chunk)
    #         if i + chunk_size >= len(words):
    #             break
    # return chunks_list
    chunks_list = []
    words = text.split()
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        chunks_list.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks_list

@app.on_event("startup")
def startup_event():
    global embed_model, client, index, chunks

    print("🚀 Đang tải mô hình Embedding và kết nối Proxy LLM...")

    if not LOCAL_MODEL_DIR.exists():
        raise RuntimeError(
            "Local model not found. Run scripts/install_vietnamese_sbert.py first."
        )

    embed_model = SentenceTransformer(str(LOCAL_MODEL_DIR))

    client = OpenAI(
        base_url=f"{SERVER_URL}/api/v1/proxy",
        api_key=STUDENT_ID
    )

    # Auto load vector db nếu tồn tại
    if Path(FAISS_PATH).exists() and Path(CHUNKS_PATH).exists():
        print("📦 Loading existing vector db...")

        index = faiss.read_index(FAISS_PATH)

        with open(CHUNKS_PATH, "rb") as f:
            chunks = pickle.load(f)

        print(
            f"✅ Loaded {len(chunks)} chunks "
            f"({index.ntotal} vectors)"
        )

class UploadRequest(BaseModel):
    doc_id: Optional[str] = None
    text: str

class UploadResponse(BaseModel):
    status: str
    doc_id: Optional[str] = None
    chunks: int

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: List[str] = []

@app.post("/upload", response_model=UploadResponse)
def receive_document(data: UploadRequest):
    global index, chunks

    # Nếu đã có vector db thì bỏ qua luôn
    if index is not None and len(chunks) > 0:
        print("📦 Vector DB đã tồn tại, bỏ qua embedding")

        return UploadResponse(
            status="success",
            doc_id=data.doc_id,
            chunks=len(chunks)
        )

    print("\n📄 NHẬN DOCUMENT: Đang tiến hành Chunking và Embedding...")

    chunks = chunk_text(
        data.text,
        chunk_size=300,
        overlap=50
    )

    print(f"   -> Đã chia tài liệu thành {len(chunks)} chunks.")

    embeddings = embed_model.encode(
        chunks,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(
        embeddings.astype("float32")
    )

    # SAVE
    faiss.write_index(index, FAISS_PATH)

    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    print("💾 Đã lưu Vector DB xuống đĩa")

    return UploadResponse(
        status="success",
        doc_id=data.doc_id,
        chunks=len(chunks)
    )

@app.post("/ask", response_model=AskResponse)
def receive_question(data: AskRequest):
    print(f"\n❓ NHẬN CÂU HỎI: {data.question[:50]}...")
    
    # Nếu chưa up document thì auto đánh bừa để ko bị lỗi
    if index is None or not chunks:
        print("   => Cảnh báo: Chưa có dữ liệu Document. Chọn bừa X!")
        return AskResponse(answer="X", sources=[])

    # 1. Retrieval
    q_emb = embed_model.encode([data.question])
    distances, indices = index.search(np.array(q_emb).astype('float32'), k=3)
    
    retrieved_contexts = [chunks[idx] for idx in indices[0]]
    context_str = "\n---\n".join(retrieved_contexts)

    print("-" * 50)
    print(context_str)
    print("-" * 50)

    # context_str = ""

    # 2. Prompting
#     prompt = f"""Dựa vào thông tin sau đây:
# {context_str}

# Hãy trả lời câu hỏi trắc nghiệm dưới đây. GIẢI THÍCH VÀ TRẢ LỜI ĐÚNG 1 KÝ TỰ (A, B, C, D)
# Câu hỏi:
# {data.question}

# Mẫu trả lời:
# Suy luận: ...
# Đáp án: X
# """

    prompt = f"""Dựa vào thông tin sau đây:
{context_str}

Hãy trả lời câu hỏi trắc nghiệm dưới đây. TRẢ LỜI ĐÚNG 1 KÝ TỰ (A, B, C, D), không giải thích!
Câu hỏi:
{data.question}"""

    llm_response = client.chat.completions.create(
        model="any",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    raw_answer = llm_response.choices[0].message.content.strip().upper()
    print(f"   => Proxy LLM trả về: {raw_answer}")

    # raw_answer = raw_answer.split("ĐÁP ÁN:")[-1].strip()  # Cố gắng lọc ra ký tự sau "Đáp án:"
    # 3. Lọc đáp án
    final_answer = "X" 
    for char in raw_answer:
        if char in ["A", "B", "C", "D", "E"]:
            final_answer = char
            break
            
    print(f"   => Proxy LLM trả về: {raw_answer} | Chốt nộp: {final_answer}")
    return AskResponse(answer=final_answer, sources=retrieved_contexts)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=LOCAL_PORT)