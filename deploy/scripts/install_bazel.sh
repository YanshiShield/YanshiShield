#!/bin/bash

set -e

mkdir -p /tmp/neursafe_fl/bazel && cd /tmp/neursafe_fl/bazel

BAZEL_VERSION=3.5.0
file=bazel-$BAZEL_VERSION-installer-linux-x86_64.sh
file_path=https://github.com/bazelbuild/bazel/releases/download/$BAZEL_VERSION/$file

curl -fSsL -O $file_path

chmod +x bazel-*.sh && ./$file

cd - && rm -rf /tmp/neursafe_fl/bazel
