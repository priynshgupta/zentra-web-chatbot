FROM python:3.9-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p uploads vector_store

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Expose the port
EXPOSE 5000

# Run the application
CMD gunicorn -k eventlet -w 1 --bind 0.0.0.0:5000 main:app
