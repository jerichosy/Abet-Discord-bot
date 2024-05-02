FROM python:3.10-slim-bookworm

RUN apt update
RUN apt install -y git \
	libpq-dev \
	build-essential
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /app
WORKDIR /app
COPY . .

CMD ["python", "bot.py"]
