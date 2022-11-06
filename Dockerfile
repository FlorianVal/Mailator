FROM python:3.7

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY app.py app.py
COPY utils utils
COPY config config

CMD ["python3" "-m" "flask" "run" "--host=0.0.0.0"]