load("@rules_python//experimental/python:wheel.bzl", "py_package", "py_wheel")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_binary(
    name = "cli_main",
    srcs = glob(["**/*.py"]),
    main = "nsfl.py",
    python_version = "PY3",
)

py_package(
    name = "cli_pkg",
    packages = [
        "neursafe_fl.python.cli",
        ],
    deps = [":cli_main"],
)

py_wheel(
    name = "nsfl",
    distribution = "nsfl",
    version = "0.1.0",
    python_tag = "py3",
    console_scripts = {
        "nsfl-ctl": "neursafe_fl.python.cli.nsfl:nsfl",
    },
    requires = [
        "click==7.1.2",
        "urllib3==1.26.4",
        "absl-py==0.11.0",
        "webdav4==0.9.7",
        "cryptography==3.3.1"
    ],
    deps = [":cli_pkg"],
)