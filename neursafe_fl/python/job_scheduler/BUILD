load("@rules_python//experimental/python:wheel.bzl", "py_package", "py_wheel")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_binary(
    name = "job_scheduler_main",
    srcs = glob(["**/*.py"]),
    main = "app.py",
    deps = [
        "//neursafe_fl/proto",
        "//neursafe_fl/python/trans",
        "//neursafe_fl/python/utils",
        "//neursafe_fl/python/libs/cloud",
        "//neursafe_fl/python/libs/db"
    ],
    python_version = "PY3",
)

py_package(
    name = "job_scheduler_pkg",
    packages = [
        "neursafe_fl.python.job_scheduler",
        "neursafe_fl.proto",
        "neursafe_fl.python.trans",
        "neursafe_fl.python.utils",
        "neursafe_fl.python.libs.cloud",
        "neursafe_fl.python.libs.db"
        ],
    deps = [":job_scheduler_main"],
)

py_wheel(
    name = "fl_job_scheduler",
    distribution = "fl_job_scheduler",
    python_tag = "py3",
    version = "0.1.0",
    requires = [
        "grpclib==0.4.1",
        "absl-py==0.11.0",
        "tornado==6.1",
        "pymongo==3.11.3",
        "psycopg2==2.7.7",
        "urllib3==1.26.4"
    ],
    deps = [":job_scheduler_pkg"],
)
