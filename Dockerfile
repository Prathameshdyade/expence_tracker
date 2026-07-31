FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

COPY requirement.txt ./
RUN pip install --no-cache-dir -r requirement.txt

COPY . .

EXPOSE 8080

CMD ["sh", "-c", "streamlit run eda_on_data.py --server.port=${PORT:-8080} --server.address=0.0.0.0"]
