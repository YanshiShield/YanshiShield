load("@rules_python//experimental/python:wheel.bzl", "py_package", "py_wheel")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_binary(
    name = "model_manager_main",
    srcs = glob(["**/*.py"]),
    main = "app.py",
    deps = [
        "//neursafe_fl/python/libs/db",
        "//neursafe_fl/python/utils",
    ],
    python_version = "PY3",
)

py_package(
    name = "model_manager_pkg",
    packages = [
        "neursafe_fl.python.model_manager",
        "neursafe_fl.python.libs.db",
        "neursafe_fl.python.utils",
        ],
    deps = [":model_manager_main"],
)

py_wheel(
    name = "fl_model_manager",
    distribution = "fl_model_manager",
    version = "0.1.0",
    python_tag = "py3",
    requires = [
        "absl-py==0.11.0",
        "tornado==6.1",
        "boto3==1.17.67",
        "pymongo==3.11.3",
        "psycopg2==2.7.7"
    ],
    deps = [":model_manager_pkg"],
)
