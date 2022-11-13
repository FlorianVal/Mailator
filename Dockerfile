FROM python:3.7-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY app.py app.py
COPY utils utils

CMD python3 app.py