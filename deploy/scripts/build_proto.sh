#!/bin/bash

set -e

CUR_DIR=$(cd $(dirname "$0");pwd)

PROJECT_DIR=$(dirname $(dirname $CUR_DIR))

rm -f $PROJECT_DIR/neursafe_fl/proto/*.py

python3 -m pip install pip --upgrade && \
python3 -m pip install h2==3.2.0 grpcio-tools==1.29.0 grpclib==0.3.2

echo "Protoc proto..."
python3 -m grpc_tools.protoc \
                 -I ${PROJECT_DIR} \
                 --python_out=${PROJECT_DIR} \
                 --grpclib_python_out=${PROJECT_DIR} \
                 ${PROJECT_DIR}/neursafe_fl/proto/*.proto
echo "Successfully protoc proto."
