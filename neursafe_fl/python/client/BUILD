load("@rules_python//experimental/python:wheel.bzl", "py_package", "py_wheel")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_binary(
    name = "client_main",
    srcs = glob(["**/*.py"]),
    main = "app.py",
    deps = [
        "//neursafe_fl/proto",
        "//neursafe_fl/python/runtime:tensorflow_runtime",
        "//neursafe_fl/python/runtime:pytorch_runtime",
        "//neursafe_fl/python/sdk:base",
        "//neursafe_fl/python/trans",
        "//neursafe_fl/python/utils",
        "//neursafe_fl/python/resource_manager",
        "//neursafe_fl/python/libs/cloud",
        "//neursafe_fl/python/libs/secure",
        "//neursafe_fl/python/libs/db",
    ],
    python_version = "PY3",
)

py_package(
    name = "client_pkg",
    packages = [
        "neursafe_fl.python.client",
        "neursafe_fl.proto",
        "neursafe_fl.python.runtime",
        "neursafe_fl.python.sdk",
        "neursafe_fl.python.trans",
        "neursafe_fl.python.utils",
        "neursafe_fl.python.resource_manager",
        "neursafe_fl.python.libs.cloud",
        "neursafe_fl.python.libs.secure",
        "neursafe_fl.python.libs.db",
        ],
    deps = [":client_main"],
)

py_wheel(
    name = "fl_client",
    distribution = "fl_client",
    version = "0.1.0",
    python_tag = "py3",
    requires = [
        "lmdb==1.3.0",
        "grpclib==0.4.1",
        "protobuf==3.14.0",
        "tensorflow==2.4.0",
        "cgroupspy==0.1.6",
        "watchdog==0.10.3",
        "absl-py==0.11.0",
        "torch==1.7.1",
        "torchvision==0.8.2",
        "nvidia-ml-py==11.450.51",
        "diffiehellman==0.13.3",
        "secret-sharing==0.2.7",
        "cryptography==3.3.1",
        "kubernetes==24.2.0",
        "psutil==5.8.0",
        "tornado==6.1",
        "pymongo==3.11.3",
        "psycopg2==2.7.7",
        "pycryptodome==3.10.1",
        "pyOpenSSL==20.0.1",
    ],
    deps = [":client_pkg"],
)

# tensorflow
py_binary(
    name = "tensorflow_client_main",
    srcs = glob(["**/*.py"]),
    main = "app.py",
    deps = [
        "//neursafe_fl/proto",
        "//neursafe_fl/python/runtime:tensorflow_runtime",
        "//neursafe_fl/python/sdk:base",
        "//neursafe_fl/python/trans",
        "//neursafe_fl/python/utils",
        "//neursafe_fl/python/resource_manager",
        "//neursafe_fl/python/libs/cloud",
        "//neursafe_fl/python/libs/secure",
        "//neursafe_fl/python/libs/db",
    ],
    python_version = "PY3",
)

py_package(
    name = "tensorflow_client_pkg",
    packages = [
        "neursafe_fl.python.client",
        "neursafe_fl.proto",
        "neursafe_fl.python.runtime",
        "neursafe_fl.python.sdk",
        "neursafe_fl.python.trans",
        "neursafe_fl.python.utils",
        "neursafe_fl.python.resource_manager",
        "neursafe_fl.python.libs.cloud",
        "neursafe_fl.python.libs.secure",
        "neursafe_fl.python.libs.db",
        ],
    deps = [":tensorflow_client_main"],
)

py_wheel(
    name = "fl_tensorflow_client",
    distribution = "fl_tensorflow_client",
    version = "0.1.0",
    python_tag = "py3",
    requires = [
        "lmdb==1.3.0",
        "grpclib==0.4.1",
        "protobuf==3.14.0",
        "tensorflow==2.4.0",
        "cgroupspy==0.1.6",
        "watchdog==0.10.3",
        "absl-py==0.11.0",
        "nvidia-ml-py==11.450.51",
        "diffiehellman==0.13.3",
        "secret-sharing==0.2.7",
        "cryptography==3.3.1",
        "kubernetes==24.2.0",
        "psutil==5.8.0",
        "tornado==6.1",
        "pymongo==3.11.3",
        "psycopg2==2.7.7",
        "pycryptodome==3.10.1",
        "pyOpenSSL==20.0.1",
    ],
    deps = [":tensorflow_client_pkg"],
)


# pytorch
py_binary(
    name = "pytorch_client_main",
    srcs = glob(["**/*.py"]),
    main = "app.py",
    deps = [
        "//neursafe_fl/proto",
        "//neursafe_fl/python/runtime:pytorch_runtime",
        "//neursafe_fl/python/sdk:base",
        "//neursafe_fl/python/trans",
        "//neursafe_fl/python/utils",
        "//neursafe_fl/python/resource_manager",
        "//neursafe_fl/python/libs/cloud",
        "//neursafe_fl/python/libs/secure",
        "//neursafe_fl/python/libs/db",
    ],
    python_version = "PY3",
)

py_package(
    name = "pytorch_client_pkg",
    packages = [
        "neursafe_fl.proto",
        "neursafe_fl.python.client",
        "neursafe_fl.python.runtime",
        "neursafe_fl.python.sdk",
        "neursafe_fl.python.trans",
        "neursafe_fl.python.utils",
        "neursafe_fl.python.resource_manager",
        "neursafe_fl.python.libs.cloud",
        "neursafe_fl.python.libs.secure",
        "neursafe_fl.python.libs.db",
        ],
    deps = [":pytorch_client_main"],
)

py_wheel(
    name = "fl_pytorch_client",
    distribution = "fl_pytorch_client",
    version = "0.1.0",
    python_tag = "py3",
    requires = [
        "lmdb==1.3.0",
        "grpclib==0.4.1",
        "protobuf==3.14.0",
        "cgroupspy==0.1.6",
        "watchdog==0.10.3",
        "torch==1.7.1",
        "torchvision==0.8.2",
        "absl-py==0.11.0",
        "nvidia-ml-py==11.450.51",
        "diffiehellman==0.13.3",
        "secret-sharing==0.2.7",
        "cryptography==3.3.1",
        "kubernetes==24.2.0",
        "psutil==5.8.0",
        "tornado==6.1",
        "pymongo==3.11.3",
        "psycopg2==2.7.7",
        "pycryptodome==3.10.1",
        "pyOpenSSL==20.0.1",
    ],
    deps = [":pytorch_client_pkg"],
)
