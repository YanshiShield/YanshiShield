FROM nsfl-base:latest

ARG FL_PROJECT_PATH=/tmp/neursafe_fl

COPY . ${FL_PROJECT_PATH}


RUN . ${FL_PROJECT_PATH}/deploy/scripts/const.properties && \
    cd ${FL_PROJECT_PATH} && \
    bazel build $cli_bazel_obj && \
    cd -

RUN . ${FL_PROJECT_PATH}/deploy/scripts/const.properties && \
    python3.7 -m pip install ${FL_PROJECT_PATH}/$cli_whl \
                            --disable-pip-version-check &&\
    rm -rf ${FL_PROJECT_PATH} ~/.cache/bazel ~/.cache/pip

CMD while true; do sleep 3600; done
