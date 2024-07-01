# app/Dockerfile

FROM python:3.12.1-bookworm

WORKDIR /app

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* 

# install Azure azd CLI
# RUN apt-get update && apt-get install -y curl bash \
#     && curl -fsSL https://aka.ms/install-azd.sh | bash

# Copy the application files into the container
COPY . /app

RUN pip install -r /app/requirements.txt

# install Microsoft ODBC Driver for SQL Server
# RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-archive-keyring.gpg \
#     && echo "deb [signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" | tee /etc/apt/sources.list.d/mssql-release.list > /dev/null \
#     && apt-get update \
#     && ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Expose port and set health check
# EXPOSE 8501
# HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Set the entry point for the container
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8501"]