load("@rules_python//python:defs.bzl", "py_library")

filegroup(
    name = "template",
    srcs = ["pod_template.json", "service_template.json"],
)

py_library(
    name = "cloud",
    srcs = glob(["**/*.py"]),
    data = [":template"],
    visibility = ["//visibility:public"],
)