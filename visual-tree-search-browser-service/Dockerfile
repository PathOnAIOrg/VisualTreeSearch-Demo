FROM mcr.microsoft.com/playwright/python:v1.41.2-jammy

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Expose the port your app runs on
EXPOSE 3000

# Set production environment
ENV APP_ENV=production

# Start the application
# Start the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]