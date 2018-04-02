ARG QGIS_TEST_VERSION=latest
FROM  qgis/qgis:${QGIS_TEST_VERSION}
MAINTAINER Matthias Kuhn <matthias@opengis.ch>

RUN apt-get update && \
    apt-get -y install default-jre

RUN apt-get -y install python3-pip

RUN pip3 install --upgrade pip

RUN pip3 install --upgrade psycopg2

ENV LANG=C.UTF-8

WORKDIR /
