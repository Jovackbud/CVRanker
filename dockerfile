# Use the official Python 3.10 image as the base
FROM python:3.10

# Expose the port Flask will run on
EXPOSE 5000

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory's contents into the container
COPY . .

# Install dependencies from requirements.txt
RUN pip install -r requirements.txt

# Run the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]
