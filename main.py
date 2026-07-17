"""FastAPI backend for AI Resume Assistant"""
import os
import json
import io
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pypdf import PdfReader
from openai import OpenAI
from prompts import SYSTEM_PROMPT, REWRITE_PROMPT, build_prompt, build_rewrite_prompt

load_dotenv()

app = FastAPI(title="AI 求职助手")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.mount("/static", StaticFiles(directory="static"), name="static")

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        content = f.read()
    from fastapi.responses import Response
    return Response(content=content, media_type="text/html", headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})


def _parse_resume(resume: UploadFile) -> str:
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="请上传 PDF 格式的简历")
    try:
        contents = resume.file.read()
        reader = PdfReader(io.BytesIO(contents))
        text = "".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF 解析失败: {e}")
    if not text.strip():
        raise HTTPException(status_code=400, detail="无法从 PDF 中提取文本")
    return text[:30000]


@app.post("/analyze")
async def analyze(resume: UploadFile = File(...), jd_text: str = Form(...)):
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="请输入岗位描述")
    resume_text = _parse_resume(resume)
    jd_truncated = jd_text[:15000]
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(resume_text, jd_truncated)}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=4096,
        )
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI 响应格式异常")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 调用失败: {e}")


@app.post("/rewrite-resume")
async def rewrite_resume(resume: UploadFile = File(...), jd_text: str = Form(...)):
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="请输入岗位描述")
    resume_text = _parse_resume(resume)
    jd_truncated = jd_text[:15000]
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": REWRITE_PROMPT},
                {"role": "user", "content": build_rewrite_prompt(resume_text, jd_truncated)}
            ],
            temperature=0.5,
            max_tokens=8192,
        )
        return {"rewritten_resume": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"优化失败: {e}")


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
