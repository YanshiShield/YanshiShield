load("@rules_python//experimental/python:wheel.bzl", "py_package", "py_wheel")
load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "base",
    srcs = glob(["*.py"]),
    deps = [
        "//neursafe_fl/python/client/workspace:workspace",
        "//neursafe_fl/python/runtime:base",
        "//neursafe_fl:neursafe_fl"
    ],
    visibility = ["//visibility:public"],
)

# all
py_library(
    name = "fl_sdk_lib",
    srcs = glob(["*.py"]),
    deps = [
        "//neursafe_fl/python/sdk:base",
        "//neursafe_fl/python/runtime:tensorflow_runtime",
        "//neursafe_fl/python/runtime:pytorch_runtime",
        "//neursafe_fl/python/libs/optimizer:optimizer",
        "//neursafe_fl/python/libs/loss:loss",
        "//neursafe_fl/python/libs/compression:compression",
    ],
    visibility = ["//visibility:public"],
)

py_package(
    name = "fl_sdk_pkg",
    packages = [
        "neursafe_fl.python.sdk",
        "neursafe_fl.python.client.workspace",
        "neursafe_fl.python.runtime",
        "neursafe_fl",
        "neursafe_fl.python.libs.optimizer",
        "neursafe_fl.python.libs.loss",
        "neursafe_fl.python.libs.compression",
        ],
    deps = [":fl_sdk_lib"],
)

py_wheel(
    name = "fl_sdk",
    distribution = "fl_sdk",
    python_tag = "py3",
    version = "0.1.0",
    requires = [
        "tensorflow==2.4.0",
        "torch==1.7.1",
        "torchvision==0.8.2",
    ],
    deps = [":fl_sdk_pkg"],
)

# tensorflow
py_library(
    name = "fl_tensorflow_sdk_lib",
    srcs = glob(["*.py"]),
    deps = [
        "//neursafe_fl/python/sdk:base",
        "//neursafe_fl/python/runtime:tensorflow_runtime",
        "//neursafe_fl/python/libs/optimizer:optimizer",
        "//neursafe_fl/python/libs/loss:loss",
        "//neursafe_fl/python/libs/compression:compression",
    ],
    visibility = ["//visibility:public"],
)

py_package(
    name = "fl_tensorflow_sdk_pkg",
    packages = [
        "neursafe_fl.python.sdk",
        "neursafe_fl.python.client.workspace",
        "neursafe_fl.python.runtime",
        "neursafe_fl",
        "neursafe_fl.python.libs.optimizer",
        "neursafe_fl.python.libs.loss",
        "neursafe_fl.python.libs.compression",
        ],
    deps = [":fl_tensorflow_sdk_lib"],
)

py_wheel(
    name = "fl_tensorflow_sdk",
    distribution = "fl_tensorflow_sdk",
    python_tag = "py3",
    version = "0.1.0",
    requires = [
        "tensorflow==2.4.0",
    ],
    deps = [":fl_tensorflow_sdk_pkg"],
)


# pytorch
py_library(
    name = "fl_pytorch_sdk_lib",
    srcs = glob(["*.py"]),
    deps = [
        "//neursafe_fl/python/sdk:base",
        "//neursafe_fl/python/runtime:pytorch_runtime",
        "//neursafe_fl/python/libs/optimizer:optimizer",
        "//neursafe_fl/python/libs/loss:loss",
        "//neursafe_fl/python/libs/compression:compression",
    ],
    visibility = ["//visibility:public"],
)

py_package(
    name = "fl_pytorch_sdk_pkg",
    packages = [
        "neursafe_fl.python.sdk",
        "neursafe_fl.python.client.workspace",
        "neursafe_fl.python.runtime",
        "neursafe_fl",
        "neursafe_fl.python.libs.optimizer",
        "neursafe_fl.python.libs.loss",
        "neursafe_fl.python.libs.compression",
        ],
    deps = [":fl_pytorch_sdk_lib"],
)

py_wheel(
    name = "fl_pytorch_sdk",
    distribution = "fl_pytorch_sdk",
    python_tag = "py3",
    version = "0.1.0",
    requires = [
        "torch==1.7.1",
        "torchvision==0.8.2",
    ],
    deps = [":fl_pytorch_sdk_pkg"],
)
