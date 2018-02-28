FROM python:3
RUN ["mkdir", "/data"]
CMD ["python", "main.py"]
WORKDIR /usr/src/app
COPY requirements.txt .
COPY main.py .
COPY config.ini .
RUN ["pip", "install", "-r", "requirements.txt"]