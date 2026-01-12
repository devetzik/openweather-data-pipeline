FROM python:3.9-slim

WORKDIR /app

# Copy the requirements file first (for better Docker caching)
COPY requirements.txt .

# Install dependencies from the file
# --no-cache-dir keeps the image small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY etl.py .

CMD ["python", "-u", "etl.py"]