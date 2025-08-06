# Use the official Python 3.10 image as the base
FROM python:3.10-slim-buster

# Install WeasyPrint system dependencies before installing Python packages
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --system --group appuser
    
# Set the working directory inside the container
WORKDIR /app

USER appuser

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port uvicorn will run on.
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
