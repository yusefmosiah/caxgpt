# Use an official Python runtime as the base image
FROM python:3.12

# Set the working directory in the container
WORKDIR /api

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Expose the port on which your FastAPI application runs (default is 8000)
EXPOSE 8000

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"]
