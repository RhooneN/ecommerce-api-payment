FROM python:3.11-slim

WORKDIR /app

ENV DJANGO_SETTINGS_MODULE=payment.settings

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN python manage.py collectstatic --noinput

COPY consul/payment.json /app/consul/payment.json
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
