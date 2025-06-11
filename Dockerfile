FROM python:3.11

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

RUN pip install . || pip install -r requirements.txt

EXPOSE 8000

# Run app
CMD ["uvicorn", "fastapi_scs.main:app", "--host", "0.0.0.0", "--port", "8000"]
