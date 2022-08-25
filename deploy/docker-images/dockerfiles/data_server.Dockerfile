FROM nsfl-base:latest

ARG FL_PROJECT_PATH=/tmp/federated-learing
COPY . ${FL_PROJECT_PATH}

RUN bash ${FL_PROJECT_PATH}/deploy/scripts/build_proto.sh

RUN . ${FL_PROJECT_PATH}/deploy/scripts/const.properties && \
    cd ${FL_PROJECT_PATH} && \
    bazel build $data_server_bazel_obj && \
    cd -

RUN . ${FL_PROJECT_PATH}/deploy/scripts/const.properties && \
    python3.7 -m pip install ${FL_PROJECT_PATH}/$data_server_whl \
                             --disable-pip-version-check&&\
    rm -rf ${FL_PROJECT_PATH} ~/.cache/bazel ~/.cache/pip

ENTRYPOINT ["python3.7", "-m", "neursafe_fl.python.data_server.app"]
