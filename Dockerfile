# Simple Dockerfile for Sophia Chat MVP
# This version is optimized for simplicity and reliability in development.

# Use a standard Python 3.12 slim image.
FROM python:3.12-slim

# Set the working directory inside the container.
WORKDIR /app

# Copy the entire project context into the container.
# This ensures all files, including frontend/ and requirements files, are present.
COPY . .

# Install Python dependencies from requirements.txt.
# The --no-cache-dir flag ensures we get a fresh install.
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the application will run on.
EXPOSE 8080

# The command to run the application using uvicorn.
# This is the same command we use for local development.
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8080"]
