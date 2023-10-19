From python:3.9-slim-buster

LABEL Name="ETL script" Version=0.1

# Working directory in the container
WORKDIR /etl

# Copy directory to the container
COPY /etl .

# Runs when image is built
# Runs when image is built
RUN apt-get update &  apt-get install -y \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && pip install --no-cache-dir -r requirements.txt


# Runs when image starts
CMD ["python3","api_requests.py"]


