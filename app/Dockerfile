FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

# Install dependencies from the file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY etl.py .

CMD ["python", "-u", "etl.py"]