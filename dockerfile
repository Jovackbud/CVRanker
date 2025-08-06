# Use the official Python 3.10 image as the base
FROM python:3.10-slim

# Install WeasyPrint system dependencies before installing Python packages
# Add fontconfig for better font handling with WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies. Use --no-cache-dir to keep the image size down.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --force-reinstall -r requirements.txt

# Get the Python executable's bin directory and add it to the PATH
RUN echo "export PATH=$PATH:$(python -m site --user-base)/bin" >> /app/setup_env.sh && \
    echo "source /app/setup_env.sh" >> /etc/profile && \
    echo "source /app/setup_env.sh" >> /home/appuser/.bashrc



# Copy the rest of the application code
# This copies as root, which is fine before switching user.
COPY . .

# Ensure the application directory is owned by the appuser
# This is important if your application needs to write files (e.g., temp files).
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose the port uvicorn will run on.
EXPOSE 8000

# Command to run the application using Uvicorn
# For production, consider increasing workers based on your DigitalOcean droplet specs.
# For example, for a 4-CPU droplet, you might use --workers 4.
# We'll start with a safe default and can adjust later.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]