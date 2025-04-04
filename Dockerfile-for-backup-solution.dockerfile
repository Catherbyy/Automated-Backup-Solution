FROM python:3.9-slim

# Install gnupg for encryption support
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Create backup directories
RUN mkdir -p /app /backups /logs /data

# Copy script and default config file
WORKDIR /app
COPY backup.py /app/
COPY backup_config.ini /app/

# Set execute permissions
RUN chmod +x /app/backup.py

# Define default environment variables
ENV BACKUP_CONFIG=/app/backup_config.ini

# Command to run the script
ENTRYPOINT ["python", "/app/backup.py"]
CMD ["--config", "/app/backup_config.ini"]