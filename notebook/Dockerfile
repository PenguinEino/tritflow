# Build from the repository root; execute as linux/amd64.
FROM ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac
ENV DEBIAN_FRONTEND=noninteractive QT_QPA_PLATFORM=offscreen
COPY notebook/docker-apt-packages.txt /tmp/docker-apt-packages.txt
RUN rm -f /etc/apt/sources.list.d/ubuntu.sources && \
    printf '%s\n' \
      'deb http://snapshot.ubuntu.com/ubuntu/20261019T000000Z/ noble main universe' \
      'deb http://snapshot.ubuntu.com/ubuntu/20261019T000000Z/ noble-updates main universe' \
      'deb http://snapshot.ubuntu.com/ubuntu/20261019T000000Z/ noble-security main universe' \
      > /etc/apt/sources.list && \
    apt-get -o Acquire::Check-Valid-Until=false -o APT::Update::Error-Mode=any update && \
    xargs -a /tmp/docker-apt-packages.txt apt-get install -y --allow-downgrades --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /opt/tritflow/source
COPY . .
RUN python3 -m venv /opt/tritflow/venv && \
    /opt/tritflow/venv/bin/python -m pip install --no-deps --require-hashes \
      --only-binary=:all: -r notebook/requirements-lock.txt && \
    /opt/tritflow/venv/bin/python notebook/setup_colab.py --source /opt/tritflow/source \
      --prefix /opt/tritflow/runtime --python-lock notebook/requirements-lock.txt
ENV PATH=/opt/tritflow/runtime/bin:/opt/tritflow/venv/bin:$PATH \
    TRITFLOW_ROOT=/opt/tritflow/source \
    KLAYOUT_BINARY=/opt/tritflow/runtime/bin/klayout \
    TRITFLOW_NOTEBOOK_HEADLESS=1
CMD ["python", "notebook/qualify_notebook.py", "--output", "/opt/tritflow/report"]
