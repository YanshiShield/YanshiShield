load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "workspace",
    srcs = glob(["*.py"]),
    deps = [
        "//neursafe_fl/python/utils",
        "//neursafe_fl/python/runtime:base",
    ],
    visibility = ["//visibility:public"],
)
