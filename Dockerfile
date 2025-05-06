# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the required files and directories
COPY requirements.txt .
COPY hcpa.py .
COPY backend/ ./backend/
COPY images/ ./images/
COPY styles/ ./styles/
COPY models/ ./models/

# Install system dependencies and clean up apt cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Run hcpa.py when the container launches
CMD ["streamlit", "run", "hcpa.py"]
