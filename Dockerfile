# Use official Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (Render expects 10000)
EXPOSE 10000

# Set environment variables
ENV PORT=10000

# Start the app with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
