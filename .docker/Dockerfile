ARG QGIS_TEST_VERSION=latest
FROM  opengisch/qgis:${QGIS_TEST_VERSION}
MAINTAINER Matthias Kuhn <matthias@opengis.ch>

# remove QGIS apt repo to avoid signing key issues
RUN add-apt-repository -r  https://qgis.org/ubuntu && \
    add-apt-repository -r  https://qgis.org/ubuntu-ltr

RUN apt-get update && \
    apt-get -y install openjdk-8-jre curl locales \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# MSSQL: client side
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | tee /etc/apt/sources.list.d/msprod.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools unixodbc unixodbc-dev libqt5sql5-odbc

COPY ./requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# Avoid sqlcmd termination due to locale -- see https://github.com/Microsoft/mssql-docker/issues/163
RUN echo "nb_NO.UTF-8 UTF-8" > /etc/locale.gen
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN locale-gen
ENV PATH="/usr/local/bin:${PATH}"

ENV LANG=C.UTF-8

WORKDIR /
