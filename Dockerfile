# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (default Flask port is 5000, change if needed)
EXPOSE 10000

# Set environment variables (optional)
ENV FLASK_ENV=production

# Start the app with Gunicorn for production
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
