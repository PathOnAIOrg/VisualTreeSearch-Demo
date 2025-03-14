FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Expose the port your app runs on
EXPOSE 3000

# Set production environment
ENV APP_ENV=production

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]