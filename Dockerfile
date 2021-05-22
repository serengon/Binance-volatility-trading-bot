FROM python:3.8
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV PYTHONPATH=/

CMD python -m app.app
