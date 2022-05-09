load("@rules_python//experimental/python:wheel.bzl", "py_package", "py_wheel")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_binary(
    name = "selector_main",
    srcs = glob(["**/*.py"]),
    main = "app.py",
    deps = [
        "//neursafe_fl/proto",
        "//neursafe_fl/python/trans",
        "//neursafe_fl/python/utils",
    ],
    python_version = "PY3",
)

py_package(
    name = "selector_pkg",
    packages = [
        "neursafe_fl.python.selector",
        "neursafe_fl.proto",
        "neursafe_fl.python.trans",
        "neursafe_fl.python.utils",
        ],
    deps = [":selector_main"],
)

py_wheel(
    name = "fl_selector",
    distribution = "fl_selector",
    version = "0.1.0",
    python_tag = "py3",
    requires = [
        "grpclib==0.4.1",
        "protobuf==3.14.0",
        "absl-py==0.11.0",
        "pycryptodome==3.10.1",
        "pyOpenSSL==20.0.1",
    ],
    deps = [":selector_pkg"],
)
