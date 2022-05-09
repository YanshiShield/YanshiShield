------

### Contributing

We welcome all kinds of contributions, there are several ways to contribute depending on what you're interested in:

- **Framework**: If you are interested in the framework process of federated learning and have a certain understanding of the basic concepts of federated learning, you are very welcome to supplement or complete the new federated learning features. In addition, you can also optimize and improve existing processes and codes. We strongly recommend that you open an issue for discussion before developing new features, so that you might get a more suitable solution.
- **Algorithm**: If you are interested in algorithms such as privacy or secure aggregation used in federated learning, then we welcome you to develop new algorithms to integrate into the framework. We have a complete set of extension mechanisms to develop new algorithms without needing to know the framework.
- **Docs**: If you are interested in helping us improve the developer experience, we also welcome you to supplement some documents, such as detailed instructions to the API, or corrections of errors in the documents.
- **Tutorials**: If you are very interested in the application of federated learning, you can try to provide examples of application scenarios, new federated learning datasets, or federated models, etc., which can help other users better understand federated learning, and its application scenarios.

Of course not limited to the above, please read the guidelines below carefully before submitting.



### Contributing Guidelines

#### Features

All submissions, including submissions by project members, require review. We use GitHub pull requests for this purpose. Consult [GitHub Help](https://help.github.com/articles/about-pull-requests/ ) for more information on using pull requests. One of the responsible code owners will then review your contribution later.

Notice: You must comply with the DCO agreement when submitting, refer to Legal Notice bellow.



#### Bugs or Issues

You are very welcome to point out any errors in the code or documentation, you can directly submit a PR to fix it. Also, you can illustrate bugs and features requests via the [GitHub issues](https://github.com/neursafe/federated-learning/issues). If you need help, ask your questions via the mailing list bellow.

- mail: 



#### Code Style

In order to better maintain the consistency of the code and make it easier for developers to understand, please following the code guidelines bellow:

- Python style:  [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/ )
- Protocol buffers style： [Protocol Buffers Style Guide](https://developers.google.com/protocol-buffers/docs/style)
- When submitting new features or fixing bugs, please attach the corresponding unittest to ensure the correctness of the code. Follow the python built-in [unittest.TestCase](https://docs.python.org/3.7/library/unittest.html)



#### PR Checklist

When you are ready to submit a PR, please check this list before submitting PR：

- Check to make sure that every commit has signed the DCO agreement, otherwise check the method [here](https://www.secondstate.io/articles/dco/) to fix it.

- Ensure that the code is statically checked by [pylint](https://pypi.org/project/pylint/), [flake8](https://pypi.org/project/flake8/) tool, you can install the tools by:

  ```
  pip install pylint flake8
  ```

- Ensure that the unittest is tested by the [pytest](https://pypi.org/project/pytest/) tool, you can install the tool by:

  ```
  pip install pytest
  ```

- Use [bazel build](https://bazel.build/) to make sure the project compiles successfully.

For simplicity, you can also execute the [tox](https://tox.wiki/en/latest/#) command in the project root directory to complete the checks 2~4 items. The process is as follows:

```
pip install tox

cd federated-learning/

tox
```

After the above checklist is passed, then you can submit the PR.



### Legal Notice

We have adopted the [DCO(Developer Certificate of Origin)](https://developercertificate.org/) as the contributor agreement, so be sure to understand the usage of the agreement before submitting. The usage method is as follows:

- [how does it works](https://probot.github.io/apps/dco/)
- [how to use it](https://www.secondstate.io/articles/dco/)

In particular, you must sign-off on every commit, otherwise the entire PR will not be accepted, the format as follows(with a single line in the commit message):

```
Signed-off-by: Full Name <email>
```
