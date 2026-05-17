from pathlib import Path

import faiss
import numpy as np
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# ================= CẤU HÌNH =================
SERVER_URL = "http://192.168.50.218:8000"  # IP Server Ban tổ chức
STUDENT_ID = "B22DCKH060"             # Mã sinh viên
LOCAL_PORT = 3636                     # Port chạy server của sinh viên 
LOCAL_MODEL_DIR = Path(__file__).resolve().parent / "models" / "vietnamese-sbert"

# ================= BIẾN TOÀN CỤC =================
app = FastAPI()
embed_model = None
client = None
index = None
chunks = []

def chunk_text(text, chunk_size=150, overlap=30):
    words = text.split()
    chunks_list = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        chunks_list.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks_list

@app.on_event("startup")
def startup_event():
    global embed_model, client
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

class UploadData(BaseModel):
    document: str

class QuestionData(BaseModel):
    question: str

@app.post("/upload")
def receive_document(data: UploadData):
    global index, chunks
    print("\n📄 NHẬN DOCUMENT: Đang tiến hành Chunking và Embedding...")
    
    chunks = chunk_text(data.document, chunk_size=150, overlap=30)
    print(f"   -> Đã chia tài liệu thành {len(chunks)} chunks.")
    
    embeddings = embed_model.encode(chunks)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))
    
    print("   -> Bơm dữ liệu vào FAISS thành công. SẴN SÀNG THI!")
    return {"message": "Processing complete"}

@app.post("/ask")
def receive_question(data: QuestionData):
    print(f"\n❓ NHẬN CÂU HỎI: {data.question[:50]}...")
    
    # Nếu chưa up document thì auto đánh bừa để ko bị lỗi
    if index is None or not chunks:
        print("   => Cảnh báo: Chưa có dữ liệu Document. Chọn bừa A!")
        return {"answer": "A"}

    # 1. Retrieval
    q_emb = embed_model.encode([data.question])
    distances, indices = index.search(np.array(q_emb).astype('float32'), k=3)
    
    retrieved_contexts = [chunks[idx] for idx in indices[0]]
    context_str = "\n---\n".join(retrieved_contexts)

    # 2. Prompting
    prompt = f"""Dựa vào thông tin sau đây:
{context_str}

Hãy trả lời câu hỏi trắc nghiệm dưới đây. CHỈ TRẢ LỜI ĐÚNG 1 KÝ TỰ (A, B, C, D), không giải thích!
Câu hỏi:
{data.question}"""

    llm_response = client.chat.completions.create(
        model="any",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    raw_answer = llm_response.choices[0].message.content.strip().upper()
    
    # 3. Lọc đáp án
    final_answer = "A" 
    for char in raw_answer:
        if char in ["A", "B", "C", "D"]:
            final_answer = char
            break
            
    print(f"   => Proxy LLM trả về: {raw_answer} | Chốt nộp: {final_answer}")
    return {"answer": final_answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=LOCAL_PORT)