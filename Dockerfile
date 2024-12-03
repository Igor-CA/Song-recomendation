# Use an official Python runtime as a base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy your project files into the container
COPY . .

# Install dependencies (use requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Streamlit runs on
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "main.py", "--server.enableCORS=false", "--server.port=8501"]
