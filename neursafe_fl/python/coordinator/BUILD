load("@rules_python//experimental/python:wheel.bzl", "py_package", "py_wheel")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_binary(
    name = "coordinator_main",
    srcs = glob(["**/*.py"]),
    main = "app.py",
    deps = [
        "//neursafe_fl/proto",
        "//neursafe_fl/python/runtime:tensorflow_runtime",
        "//neursafe_fl/python/runtime:pytorch_runtime",
        "//neursafe_fl/python/trans",
        "//neursafe_fl/python/utils",
        "//neursafe_fl/python/libs/secure",
        "//neursafe_fl/python/libs/optimizer",
    ],
    python_version = "PY3",
)

py_package(
    name = "coordinator_pkg",
    packages = [
        "neursafe_fl.python.coordinator",
        "neursafe_fl.proto",
        "neursafe_fl.python.runtime",
        "neursafe_fl.python.trans",
        "neursafe_fl.python.utils",
        "neursafe_fl.python.libs.secure",
        "neursafe_fl.python.libs.optimizer"
        ],
    deps = [":coordinator_main"],
)

py_wheel(
    name = "fl_coordinator",
    distribution = "fl_coordinator",
    python_tag = "py3",
    version = "0.1.0",
    requires = [
        "grpclib==0.4.1",
        "tensorflow==2.4.0",
        "absl-py==0.11.0",
        "torch==1.7.1",
        "torchvision==0.8.2",
        "diffiehellman==0.13.3",
        "secret-sharing==0.2.7",
        "cryptography==3.3.1",
        "tornado==6.1",
        "pymongo==3.11.3"
    ],
    deps = [":coordinator_pkg"],
)
