# Description: Dockerfile for the Streamlit and FastAPI application

# Use Python base image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the application files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Start both FastAPI and Streamlit
CMD uvicorn app:app --host 0.0.0.0 --port 8000 & streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
