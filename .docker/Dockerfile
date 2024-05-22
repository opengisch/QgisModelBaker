ARG QGIS_TEST_VERSION=latest
FROM  qgis/qgis:${QGIS_TEST_VERSION}

RUN apt-get update && \
    apt-get -y install openjdk-8-jre \
    && rm -rf /var/lib/apt/lists/*

# Useful only in 3.22 and 3.28: drop when not need anymore
RUN apt-get update && apt-get -y install python3-pip python3-venv python3-pytest python3-wheel

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv --system-site-packages $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY ./requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /
