FROM python:3.10.11

# Set working directory and copy files
WORKDIR /app
COPY requirements.txt /app

# Install dependencies
RUN apt-get update && \
    apt-get install curl --no-install-recommends -y && \
    sqlite3 \
    libsqlite3-dev \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application files
COPY src/ /app/src

# Set the entrypoint to run Streamlit with the specified app
ENTRYPOINT ["streamlit", "run", "src/1_🏠_Home.py"]