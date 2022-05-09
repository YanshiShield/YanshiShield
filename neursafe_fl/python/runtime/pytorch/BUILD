load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "pytorch",
    srcs = glob(["*.py"]),
    deps = [
        "//neursafe_fl/python/runtime:base",
        "//neursafe_fl/python/libs/secure:secure",
    ],
    visibility = ["//visibility:public"],
)
