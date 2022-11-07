FROM tensorflow/tensorflow:2.4.0-gpu

LABEL com.nvidia.volumes.needed=nvidia_driver

RUN apt-get update -m; exit 0

RUN apt-get install -y python3.7 python3.7-dev &&\
    apt-get install -y python3-pip

RUN ln -s -f /usr/bin/python3.7 /usr/bin/python
RUN ln -s -f /usr/bin/python3.7 /usr/bin/python3

COPY deploy/scripts/install_bazel.sh /tmp/install_bazel.sh

RUN bash /tmp/install_bazel.sh && \
    rm -f /tmp/install_bazel.sh && \
    apt install -y s3fs && \
    apt-get clean && \
    rm -rf /tmp/install_bazel.sh

COPY requirements.txt /tmp/neursafe_fl/requirements.txt

RUN sed s/tensorflow==2.4.0/tensorflow-gpu==2.4.0/g -i /tmp/neursafe_fl/requirements.txt

RUN python3.7 -m pip install --upgrade pip

RUN python3.7 -m pip install -r /tmp/neursafe_fl/requirements.txt && \
    rm -rf /tmp/neursafe_fl/requirements.txt

ARG FL_PROJECT_PATH=/tmp/federated-learning
COPY . ${FL_PROJECT_PATH}

RUN apt-get install -y git

RUN bash ${FL_PROJECT_PATH}/deploy/scripts/build_proto.sh

RUN sed s/tensorflow==2.4.0/tensorflow-gpu==2.4.0/g -i ${FL_PROJECT_PATH}/neursafe_fl/python/client/BUILD
RUN sed s/tensorflow==2.4.0/tensorflow-gpu==2.4.0/g -i ${FL_PROJECT_PATH}/neursafe_fl/python/sdk/BUILD

RUN . ${FL_PROJECT_PATH}/deploy/scripts/const.properties && \
    cd ${FL_PROJECT_PATH} && \
    bazel build $client_bazel_obj && \
    bazel build $sdk_bazel_obj && \
    cd -

RUN . ${FL_PROJECT_PATH}/deploy/scripts/const.properties && \
    python3.7 -m pip install ${FL_PROJECT_PATH}/$client_whl \
                            --disable-pip-version-check &&\
    python3.7 -m pip install ${FL_PROJECT_PATH}/$sdk_whl \
                            --disable-pip-version-check &&\
    rm -rf ${FL_PROJECT_PATH} ~/.cache/bazel ~/.cache/pip

ENTRYPOINT ["python3.7", "-m", "neursafe_fl.python.client.app"]
