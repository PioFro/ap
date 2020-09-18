FROM python:3
MAINTAINER Piotr Frohlich
COPY . /app
WORKDIR /app
ENV ctrl_url="localhost:4444/autopolicy/"
RUN pip install -r ./requirements.txt
EXPOSE 1111
CMD python3 ./app.py $ctrl_url