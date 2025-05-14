# product_service/Dockerfile
FROM python:3.12-slim 

WORKDIR /code

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./app/ /code/app/  

RUN ls -la /code/app
RUN ls -la /code/app/api # Emin olmak için bir alt dizini daha kontrol et

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "debug"]
