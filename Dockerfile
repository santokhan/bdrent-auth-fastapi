FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# RUN apt-get update && apt-get install -y git \
#     && rm -rf /var/lib/apt/lists/*

# RUN git --version

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0"]