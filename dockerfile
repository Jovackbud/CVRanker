# Use the official Python 3.10 image as the base
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port uvicorn will run on.
# Render provides the port number via the PORT environment variable.
# We'll use 8000 as a standard default for FastAPI.
EXPOSE 8000

# Command to run the application using Uvicorn
# It will listen on the port provided by Render's $PORT env var, or 8000.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
