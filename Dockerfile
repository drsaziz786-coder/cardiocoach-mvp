# --- Base Image ---
FROM python:3.10-slim

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- Install OS Packages ---
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    build-essential \
    poppler-utils \
    && apt-get clean

# --- Set Work Directory ---
WORKDIR /app

# --- Install Python Dependencies ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy Application Files ---
COPY . .

# --- Expose Port ---
EXPOSE 8000

# --- Launch App ---
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
