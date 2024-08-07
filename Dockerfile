FROM python:3.10-bookworm

# Set working directory and copy files
WORKDIR /app
COPY requirements.txt /app

# Install dependencies
RUN apt-get update && \
    apt-get install curl --no-install-recommends -y && \
    apt-get install sqlite3 --no-install-recommends -y && \
    apt-get install libsqlite3-dev --no-install-recommends -y && \
    apt-get install libsm6 libxext6 ffmpeg libfontconfig1 libxrender1 libgl1-mesa-glx -y && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install pysqlite3-binary

# Copy application files
COPY src/ /app/src

# Set the entrypoint to run Streamlit with the specified app
ENTRYPOINT ["streamlit", "run", "src/1_🤖_Raggie.py"]