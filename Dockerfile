FROM python:3.12-slim

WORKDIR /app
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

COPY . .

# Run the web-relevant tests headless as part of the build (no Qt needed).
RUN python -m pytest tests/core tests/io tests/web

EXPOSE 8000
CMD ["uvicorn", "sorting_visualizer.web.server:app", "--host", "0.0.0.0", "--port", "8000"]
