# Use python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all files from current folder to the container
COPY . ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Open the port Streamlit uses (8080 is default for Cloud Run)
EXPOSE 8080

# Command to run the app
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]