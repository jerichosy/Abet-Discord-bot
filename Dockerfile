FROM python:3.10-slim-bookworm

RUN apt update
RUN apt install -y git \
	libpq-dev \
	build-essential \
	poppler-utils

RUN mkdir /app
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
