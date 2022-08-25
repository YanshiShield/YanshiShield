load("@rules_python//experimental/python:wheel.bzl", "py_package", "py_wheel")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_binary(
    name = "data_server_main",
    srcs = glob(["**/*.py"]),
    main = "app.py",
    deps = [
        "//neursafe_fl/python/utils",
    ],
    python_version = "PY3",
)

py_package(
    name = "data_server_pkg",
    packages = [
        "neursafe_fl.python.data_server",
        "neursafe_fl.python.utils",
        ],
    deps = [":data_server_main"],
)

py_wheel(
    name = "fl_data_server",
    distribution = "fl_data_server",
    version = "0.1.0",
    python_tag = "py3",
    requires = [
        "WsgiDAV==4.0",
        "boto3==1.17.67",
        "cheroot==8.6.0"
    ],
    deps = [":data_server_pkg"],
)
