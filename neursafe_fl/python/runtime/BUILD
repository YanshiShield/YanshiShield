load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "base",
    srcs = glob(["*.py"]),
    visibility = ["//visibility:public"],
)

py_library(
    name = "tensorflow_runtime",
    srcs = glob(["*.py"]),
    deps = [
        "//neursafe_fl/python/runtime/tensorflow",
    ],
    visibility = ["//visibility:public"],
)

py_library(
    name = "pytorch_runtime",
    srcs = glob(["*.py"]),
    deps = [
        "//neursafe_fl/python/runtime/pytorch",
    ],
    visibility = ["//visibility:public"],
)
