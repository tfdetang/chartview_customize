FROM ubuntu:16.04

MAINTAINER Weikunt <weikun.t@google.com>

RUN sed -i s@archive.ubuntu.com@mirrors.163.com@g /etc/apt/sources.list

RUN apt-get update && apt-get install -y build-essential python3-pip python3-dev \
    libxml2 libxml2-dev libxslt-dev python3-lxml

RUN mkdir /FlaskApp

COPY FlaskApp /FlaskApp/

COPY ./requirements.txt /build/

RUN pip3 install -i https://pypi.doubanio.com/simple -r /build/requirements.txt

RUN pip3 install -i https://pypi.doubanio.com/simple tushare