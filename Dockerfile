FROM python:3
MAINTAINER Piotr Frohlich
COPY . /app
WORKDIR /app
ENV ctrl_url="localhost:4444/autopolicy/"
ENV mongo_db="172.17.0.1"
ENV out_addr="172.17.0.2"
RUN pip install -r ./requirements.txt
EXPOSE 1111
CMD python3 ./app.py $ctrl_url $mongo_db $out_addr