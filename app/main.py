import os
import io
import base64
import textwrap

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import httpx

from PIL import Image
import pytesseract
from pdfminer.high_level import extract_text
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="CardioCoach MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Pydantic models ---------- #

class SummaryRequest(BaseModel):
    text: str


class ChatRequest(BaseModel):
    message: str
    context: str = ""   # summary/explanation text


class ImageOCRRequest(BaseModel):
    image_base64: str   # "data:image/jpeg;base64,...."


class PdfOCRRequest(BaseModel):
    pdf_base64: str     # "data:application/pdf;base64,...."


class PdfSummaryRequest(BaseModel):
    summary: str


# ---------- OpenAI helper ---------- #

async def call_openai_chat(
    messages: list[dict],
    model: str = "gpt-4o",
    max_tokens: int = 800,
    temperature: float = 0.1,
) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=40.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ---------- OCR helpers ---------- #

def ocr_from_base64_image(image_base64: str) -> str:
    """
    Decode base64 image (data URL or raw base64) and run OCR using Tesseract.
    Designed for clear, printed discharge letters.
    """
    if "," in image_base64:
        _, b64data = image_base64.split(",", 1)
    else:
        b64data = image_base64

    try:
        image_bytes = base64.b64decode(b64data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image data")

    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not open image")

    img = img.convert("L")  # grayscale

    try:
        text = pytesseract.image_to_string(img, lang="eng")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")

    text = text.strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the image. "
                   "Please ensure the photo is sharp, well-lit and fills the frame.",
        )

    # light cleanup
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join([line for line in lines if line])
    return cleaned

def text_from_pdf_base64(pdf_base64: str) -> str:
    """
    Extract text from a text-based PDF (e.g. electronic letter / NHS app download).
    Does NOT run OCR on scanned PDFs – for printed letters, use the photo upload instead.
    """
    if "," in pdf_base64:
        _, b64data = pdf_base64.split(",", 1)
    else:
        b64data = pdf_base64

    try:
        pdf_bytes = base64.b64decode(b64data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid PDF data")

    # Safety limit: don't attempt huge PDFs
    max_size_mb = 8
    if len(pdf_bytes) > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"PDF is too large (> {max_size_mb} MB). Please upload a shorter letter.",
        )

    try:
        buffer = io.BytesIO(pdf_bytes)
        text = extract_text(buffer)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read text from this PDF. It may be a scanned image-only PDF. "
                   "For printed letters, please take a clear photo and use the photo option instead.",
        )

    text = (text or "").strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in this PDF. "
                   "Currently only text-based PDFs are supported. "
                   "For printed letters, please use the photo option.",
        )

    return text

# ---------- PDF generation helper ---------- #

def create_summary_pdf(summary: str) -> io.BytesIO:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "CardioCoach Summary")
    y -= 10
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Generated by CardioCoach MVP – for education only, not a substitute for clinical care.")
    y -= 25

    # Body
    c.setFont("Helvetica", 11)
    text_obj = c.beginText(50, y)

    paragraphs = summary.split("\n\n")
    for para in paragraphs:
        lines = textwrap.wrap(para.strip(), 90) if para.strip() else [""]
        for line in lines:
            text_obj.textLine(line)
        text_obj.textLine("")  # blank line between paragraphs

    text_obj.textLine("")
    text_obj.textLine("---")
    text_obj.textLine("This explanation does not replace advice from your cardiologist, GP or emergency services.")
    text_obj.textLine("If you develop chest pain, severe breathlessness, collapse, stroke-like symptoms or heavy")
    text_obj.textLine("bleeding, seek urgent medical help (999 / A&E).")

    c.drawText(text_obj)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# ---------- Frontend page ---------- #

@app.get("/", response_class=HTMLResponse)
async def index():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>CardioCoach MVP</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background:#f3f4f6;
      margin:0;
      padding:0;
    }
    .container {
      max-width: 960px;
      margin:0 auto;
      padding:16px;
    }
    .card {
      background:#fff;
      border-radius:12px;
      padding:16px;
      margin-bottom:16px;
      box-shadow:0 2px 8px rgba(15,23,42,0.08);
    }
    h1,h2 {
      margin:0 0 8px 0;
    }
    .subtitle {
      font-size:14px;
      color:#4b5563;
      margin-bottom:4px;
    }
    label {
      font-weight:600;
      display:block;
      margin-top:8px;
      margin-bottom:4px;
      font-size:14px;
    }
    textarea, input[type="text"] {
      width:100%;
      box-sizing:border-box;
      border-radius:8px;
      border:1px solid #d1d5db;
      padding:10px;
      font-size:14px;
      font-family:inherit;
    }
    textarea {
      min-height:140px;
      resize:vertical;
    }
    .file-row {
      display:flex;
      flex-wrap:wrap;
      gap:8px;
      align-items:center;
      margin-top:4px;
      margin-bottom:6px;
    }
    input[type="file"] {
      font-size:13px;
    }
    .btn {
      background:#2563eb;
      color:#fff;
      border:none;
      border-radius:999px;
      padding:10px 18px;
      font-size:14px;
      font-weight:600;
      cursor:pointer;
      margin-top:10px;
    }
    .btn.secondary {
      background:#6b7280;
    }
    .btn:disabled {
      background:#9ca3af;
      cursor:default;
    }
    .small {
      font-size:13px;
      color:#6b7280;
    }
    .banner {
      background:#FEF3C7; /* soft amber */
      color:#B45309;
      padding:6px 10px;
      border-radius:999px;
      font-size:13px;
      margin-top:10px;
      display:inline-block;
    }
    .privacy {
      font-size:12px;
      color:#6b7280;
      margin-top:8px;
      display:flex;
      align-items:center;
      gap:6px;
    }
    .privacy strong {
      font-weight:600;
    }
    .lock {
      font-size:14px;
    }
    .section-title {
      font-size:15px;
      font-weight:700;
      margin-top:12px;
      margin-bottom:4px;
    }
    .output-block {
      background:#f9fafb;
      border-radius:8px;
      padding:8px 10px;
      font-size:14px;
      white-space:pre-wrap;
      min-height:40px;
    }
    .error {
      color:#b91c1c;
      font-size:13px;
      margin-top:6px;
    }
    .chat-box {
      margin-top:10px;
    }
    .chat-log {
      background:#f9fafb;
      border-radius:8px;
      padding:8px;
      min-height:80px;
      max-height:220px;
      overflow-y:auto;
      font-size:14px;
    }
    .chat-msg-user {
      text-align:right;
      margin-bottom:4px;
    }
    .chat-msg-assistant {
      text-align:left;
      margin-bottom:4px;
    }
    .chat-bubble-user {
      display:inline-block;
      background:#2563eb;
      color:#fff;
      border-radius:12px 2px 12px 12px;
      padding:6px 10px;
    }
    .chat-bubble-assistant {
      display:inline-block;
      background:#e5e7eb;
      color:#111827;
      border-radius:2px 12px 12px 12px;
      padding:6px 10px;
    }
    .disclaimer {
      font-size:12px;
      color:#6b7280;
      margin-top:8px;
    }
    .disclaimer strong {
      font-weight:700;
    }
    .disclaimer ul {
      padding-left:18px;
      margin:4px 0 0 0;
    }
    @media (max-width: 640px) {
      .container {
        padding:8px;
      }
      .card {
        padding:12px;
      }
      textarea {
        min-height:160px; /* thumb-friendly on mobile */
      }
      .banner {
        font-size:12px;
        padding:5px 8px;
      }
      .file-row {
        flex-direction:column;
        align-items:flex-start;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <h1>🫀 CardioCoach MVP</h1>
      <p class="subtitle">Simplifies hospital discharge letters into plain English.</p>
      <p class="small">
        Paste an <strong>anonymized</strong> cardiac discharge summary or upload a clear photo
        of your printed letter, or a text-based PDF. CardioCoach will generate a simple explanation
        and answer follow-up questions. This is for education only and does <strong>not replace</strong>
        your doctors or emergency services.
      </p>
      <span class="banner">⚠️ If you feel very unwell, call 999 / 112 or attend A&amp;E.</span>
      <p class="privacy">
        <span class="lock">🔒</span>
        <span>Your text is processed securely for this session and <strong>not stored</strong> in this MVP.</span>
      </p>
    </div>

    <div class="card">
      <h2>1. Provide your discharge information</h2>

      <label for="discharge">Option A: Paste discharge summary text</label>
      <textarea id="discharge" placeholder="Paste the hospital letter here (remove your name, NHS number, address, etc.)"></textarea>

      <p class="small" style="margin-top:12px; margin-bottom:4px;"><strong>OR</strong></p>

      <label for="photoInput">Option B: Upload a clear photo of your printed letter</label>
      <div class="file-row">
        <input type="file" id="photoInput" accept="image/*" />
        <button class="btn secondary" id="photoBtn">Extract text from photo</button>
      </div>
      <div id="ocrImageStatus" class="small"></div>

      <p class="small" style="margin-top:8px; margin-bottom:4px;"><strong>OR</strong></p>

      <label for="pdfInput">Option C: Upload a PDF discharge letter</label>
      <div class="file-row">
        <input type="file" id="pdfInput" accept="application/pdf" />
        <button class="btn secondary" id="pdfBtn">Extract text from PDF</button>
      </div>
      <div id="ocrPdfStatus" class="small"></div>

      <button class="btn" id="summarizeBtn">Generate CardioCoach explanation</button>
      <div id="status" class="small"></div>
      <div id="error" class="error"></div>
    </div>

    <div class="card" id="summaryCard" style="display:none;">
      <h2>2. Explanation</h2>
      <div class="section-title">🩺 What CardioCoach says</div>
      <div class="output-block" id="summaryOutput"></div>
      <button class="btn secondary" id="downloadPdfBtn" style="margin-top:10px;">Download this summary as PDF</button>
      <p class="disclaimer">
        <strong>Important:</strong>
        <ul>
          <li>This summary may contain errors or omissions.</li>
          <li>Always check against your official hospital letter.</li>
          <li>CardioCoach does <strong>not replace</strong> your cardiologist, GP, or emergency services.</li>
        </ul>
      </p>
    </div>

    <div class="card" id="chatCard" style="display:none;">
      <h2>3. Ask CardioCoach a question</h2>
      <div class="chat-log" id="chatLog"></div>
      <div class="chat-box">
        <label for="chatInput">Your question</label>
        <textarea id="chatInput" rows="3" placeholder="Ask about your diagnosis, medicines or recovery..."></textarea>
        <button class="btn" id="chatBtn">Ask</button>
        <div id="chatError" class="error"></div>
      </div>
      <p class="disclaimer">
        If you have chest pain, severe breathlessness, collapse, stroke-like symptoms or heavy bleeding,
        please <strong>do not rely on this tool</strong> – seek urgent medical help (999 / A&amp;E).
      </p>
    </div>
  </div>

  <script>
    const summarizeBtn = document.getElementById('summarizeBtn');
    const statusEl = document.getElementById('status');
    const errorEl = document.getElementById('error');
    const dischargeEl = document.getElementById('discharge');
    const summaryCard = document.getElementById('summaryCard');
    const summaryOutput = document.getElementById('summaryOutput');
    const chatCard = document.getElementById('chatCard');
    const chatLog = document.getElementById('chatLog');
    const chatInput = document.getElementById('chatInput');
    const chatBtn = document.getElementById('chatBtn');
    const chatError = document.getElementById('chatError');
    const photoInput = document.getElementById('photoInput');
    const photoBtn = document.getElementById('photoBtn');
    const ocrImageStatus = document.getElementById('ocrImageStatus');
    const pdfInput = document.getElementById('pdfInput');
    const pdfBtn = document.getElementById('pdfBtn');
    const ocrPdfStatus = document.getElementById('ocrPdfStatus');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');

    let currentSummary = "";

    // Paste / OCR text -> summarize
    summarizeBtn.addEventListener('click', async () => {
      errorEl.textContent = "";
      statusEl.textContent = "";
      summaryCard.style.display = "none";
      chatCard.style.display = "none";
      chatLog.innerHTML = "";
      currentSummary = "";

      const text = dischargeEl.value.trim();
      if (!text) {
        errorEl.textContent = "Please paste the discharge summary text or use photo/PDF extraction first.";
        return;
      }

      summarizeBtn.disabled = true;
      statusEl.textContent = "Generating explanation...";

      try {
        const resp = await fetch('/summarize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          throw new Error(data.detail || data.error || "Request failed");
        }
        const data = await resp.json();
        currentSummary = data.summary || "";
        summaryOutput.textContent = currentSummary;
        summaryCard.style.display = "block";
        chatCard.style.display = "block";
        statusEl.textContent = "Explanation generated.";
      } catch (err) {
        console.error(err);
        errorEl.textContent = "Error: " + err.message;
      } finally {
        summarizeBtn.disabled = false;
      }
    });

    // Upload photo -> OCR -> put text into textarea
    photoBtn.addEventListener('click', async () => {
      ocrImageStatus.textContent = "";
      errorEl.textContent = "";

      const file = photoInput.files && photoInput.files[0];
      if (!file) {
        ocrImageStatus.textContent = "Please choose a photo of your letter first.";
        return;
      }

      photoBtn.disabled = true;
      ocrImageStatus.textContent = "Reading text from your photo...";

      const reader = new FileReader();
      reader.onload = async () => {
        const base64 = reader.result; // data:image/...;base64,...
        try {
          const resp = await fetch('/ocr_image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image_base64: base64 })
          });
          const data = await resp.json();
          if (!resp.ok || data.error) {
            throw new Error(data.detail || data.error || "Image reading failed");
          }
          if (data.raw_text) {
            dischargeEl.value = data.raw_text;
          }
          ocrImageStatus.textContent = "Text extracted from photo. You can edit it above before generating the explanation.";
        } catch (err2) {
          console.error(err2);
          ocrImageStatus.textContent = "Error: " + err2.message;
        } finally {
          photoBtn.disabled = false;
        }
      };
      reader.readAsDataURL(file);
    });

    // Upload PDF -> extract -> put text into textarea
    pdfBtn.addEventListener('click', async () => {
      ocrPdfStatus.textContent = "";
      errorEl.textContent = "";

      const file = pdfInput.files && pdfInput.files[0];
      if (!file) {
        ocrPdfStatus.textContent = "Please choose a PDF letter first.";
        return;
      }

      pdfBtn.disabled = true;
      ocrPdfStatus.textContent = "Reading text from your PDF...";

      const reader = new FileReader();
      reader.onload = async () => {
        const base64 = reader.result; // data:application/pdf;base64,...
        try {
          const resp = await fetch('/ocr_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pdf_base64: base64 })
          });
          const data = await resp.json();
          if (!resp.ok || data.error) {
            throw new Error(data.detail || data.error || "PDF reading failed");
          }
          if (data.raw_text) {
            dischargeEl.value = data.raw_text;
          }
          ocrPdfStatus.textContent = "Text extracted from PDF. You can edit it above before generating the explanation.";
        } catch (err2) {
          console.error(err2);
          ocrPdfStatus.textContent = "Error: " + err2.message;
        } finally {
          pdfBtn.disabled = false;
        }
      };
      reader.readAsDataURL(file);
    });

    function appendChat(role, text) {
      const wrapper = document.createElement('div');
      wrapper.className = role === 'user' ? 'chat-msg-user' : 'chat-msg-assistant';
      const bubble = document.createElement('span');
      bubble.className = role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant';
      bubble.textContent = text;
      wrapper.appendChild(bubble);
      chatLog.appendChild(wrapper);
      chatLog.scrollTop = chatLog.scrollHeight;
    }

    chatBtn.addEventListener('click', async () => {
      chatError.textContent = "";
      const question = chatInput.value.trim();
      if (!question) return;

      if (!currentSummary) {
        chatError.textContent = "Please generate your CardioCoach explanation first.";
        return;
      }

      appendChat('user', question);
      chatInput.value = "";
      chatBtn.disabled = true;

      try {
        const resp = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: question,
            context: currentSummary
          })
        });
        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          throw new Error(data.detail || data.error || "Chat failed");
        }
        const data = await resp.json();
        appendChat('assistant', data.answer || "");
      } catch (err) {
        console.error(err);
        chatError.textContent = "Error: " + err.message;
      } finally {
        chatBtn.disabled = false;
      }
    });

    // Download explanation as PDF (backend-generated)
    downloadPdfBtn.addEventListener('click', async () => {
      if (!currentSummary) return;
      try {
        const resp = await fetch('/generate_pdf', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ summary: currentSummary })
        });
        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          throw new Error(data.detail || data.error || "PDF generation failed");
        }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'cardiocoach-summary.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error(err);
        alert("Error generating PDF: " + err.message);
      }
    });
  </script>
</body>
</html>
    """
    return HTMLResponse(content=html)


# ---------- API endpoints ---------- #

@app.post("/summarize")
async def summarize(req: SummaryRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    prompt = f"""
You are CardioCoach, a UK cardiology patient education assistant.

The text below is a hospital discharge summary for a cardiac admission.

TASK:
1. Extract the key diagnosis, what treatment was done, and which heart medications were started.
2. Write a clear, kind, supportive explanation in simple language (age ~12 reading level).
3. Do NOT change medications or give new instructions.
4. Do NOT diagnose or reassure about new symptoms. Education only.

Discharge summary:
\"\"\"{req.text}\"\"\"
"""

    content = await call_openai_chat(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o",
        max_tokens=800,
        temperature=0.1,
    )
    return {"summary": content}


@app.post("/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")

    prompt = f"""
You are CardioCoach, a safe cardiology education assistant.

RULES:
- You are NOT allowed to diagnose or change treatment.
- You must NOT tell the patient that worrying symptoms are definitely safe.
- If the patient describes: new or worsening chest pain, severe breathlessness,
  collapse, stroke-like symptoms, or major bleeding, you MUST advise them to seek
  urgent medical care (999 / A&E).
- Use simple, friendly UK English.

Patient context (from their discharge summary and explanation):
\"\"\"{req.context}\"\"\"

Patient question:
\"\"\"{req.message}\"\"\"

Now answer with a clear, calm explanation for the patient.
Do NOT include JSON, just the answer text.
"""

    content = await call_openai_chat(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o",
        max_tokens=600,
        temperature=0.2,
    )
    return {"answer": content}


@app.post("/ocr_image")
async def ocr_image(req: ImageOCRRequest):
    """
    Accepts base64-encoded image (photo of printed letter) and returns extracted text.
    """
    text = ocr_from_base64_image(req.image_base64)
    return {"raw_text": text}


@app.post("/ocr_pdf")
async def ocr_pdf(req: PdfOCRRequest):
    """
    Accepts base64-encoded PDF (text-based discharge letter) and returns extracted text.
    """
    text = text_from_pdf_base64(req.pdf_base64)
    return {"raw_text": text}


@app.post("/generate_pdf")
async def generate_pdf(req: PdfSummaryRequest):
    """
    Generate a simple PDF file containing the CardioCoach summary and a disclaimer.
    """
    if not req.summary.strip():
        raise HTTPException(status_code=400, detail="Summary is empty")

    buf = create_summary_pdf(req.summary)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="cardiocoach-summary.pdf"'},
    )
