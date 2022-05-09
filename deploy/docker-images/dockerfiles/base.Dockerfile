FROM python:3.7.8

COPY deploy/scripts/install_bazel.sh /tmp/install_bazel.sh

RUN bash /tmp/install_bazel.sh && \
    rm -f /tmp/install_bazel.sh

COPY requirements.txt /tmp/neursafe_fl/requirements.txt

SHELL ["/bin/bash", "-c"]

RUN python3.7 -m pip install -r /tmp/neursafe_fl/requirements.txt && \
    \
    rm -rf ~/.cache/pip /tmp/neursafe_fl
