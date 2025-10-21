# Simple Dockerfile for Sophia Chat MVP
# This version uses a custom run script for robust logging.

FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# **THE FIX (for Scenario 5):**
# Run the application via the custom `run.py` script.
# This ensures our programmatic logging configuration is always used,
# providing reliable and detailed logs.
CMD ["python", "run.py"]
