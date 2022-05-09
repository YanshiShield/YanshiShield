load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")  # Depends on Git.
git_repository(
    name = "rules_python",
    remote = "https://github.com/bazelbuild/rules_python.git",
    commit = "c064f70",
)
load("@rules_python//python:repositories.bzl", "py_repositories")
py_repositories() # Install requirements for rules_python repositories.
