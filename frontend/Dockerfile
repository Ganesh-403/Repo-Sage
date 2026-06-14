FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    streamlit==1.41.1 \
    requests==2.32.3

# Copy Streamlit config
COPY .streamlit/ .streamlit/

# Copy application
COPY . .

EXPOSE 8501

# Streamlit-specific config
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

CMD ["streamlit", "run", "app.py"]
