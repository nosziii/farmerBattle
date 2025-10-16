# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install netcat
RUN apt-get update && apt-get install -y netcat-openbsd

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY ./app /app/app

# Copy the wait script
COPY wait-for-postgres.sh .
RUN chmod +x wait-for-postgres.sh

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the wait script and then the app
CMD ["./wait-for-postgres.sh", "db", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
