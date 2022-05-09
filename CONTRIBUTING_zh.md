------

### Contributing

我们欢迎各种形式的贡献，包括但不局限于如下几种形式：

- 框架代码：如果你对联邦学习的框架流程感兴趣，并且对联邦学习的基本概念有一定的了解，那么非常欢迎你来补充、或完成新的联邦学习流程，当然也可以针对现有流程、代码进行优化改进。我们强烈建议你在开发新的特性前，能够提出issue进行讨论，从而能够得到更合适的解决方案。
- 算法：如果你对联邦学习中用到的隐私、安全聚合等算法方面感兴趣，那么我们非常欢迎你开发新的算法来融入到框架中。我们有一套完整的扩展机制，可以在无需了解框架的情况下，开发新的算法。
- 文档：如果你有兴趣帮助我们提升开发者的体验，那么我们也非常欢迎你能够对一些文档进行补充，对接口进行详细的说明，以及文档中错误进行订正。
- 使用案例：如果你对联邦学习的应用非常感兴趣，你可以尝试进行提供应用场景的示例、新的联邦学习数据集、亦或是联邦模型等等，可以帮助其他的使用者更好的了解联邦学习、以及其应用场景。

请在提交前仔细阅读下面的指导。



### Contributing Guidelines

#### 开发

所有的提交，包括项目成员的提交，都需要经过代码审查，我们采用Github pull request的机制来进行。如果你对pull request还不了解，请查看此[帮助](https://help.github.com/articles/about-pull-requests/ )来了解更多信息。当你提交pull request后，稍后将会有项目的相关负责人员来进行代码审查。

注意：在提交前你必须遵守DCO协议，具体请参考下面贡献者协议说明。



#### 问题

我们非常欢迎指出代码或者文档中的任何错误，你可以直接提出PR来修正。同样，你也可以先通过[Github issues](https://github.com/neursafe/federated-learning/issues)提出问题或者新特性进行讨论。如果你需要帮助，可以通过下面的方式联系我们。

- 邮箱：



#### 代码规范

为了更好的保持代码的一致性，更加有利于开发者的理解，请遵守下面的一些代码规范：

- Python style： [Python开发规范](https://peps.python.org/pep-0008/ )
- Protocol buffers style： [Protocol buffers开发规范](https://developers.google.com/protocol-buffers/docs/style )
- 在提交新的特性或者修复bug时，请附带相应的unittest以保证代码的正确性，unittest请参考Python built-in [unittest.TestCase](https://docs.python.org/3.7/library/unittest.html)



#### 拉取请求

当你完成了修改准备提交PR时，请务必在提交前做以下几项检查：

1. 检查确保每一次的commit都签署了DCO协议，否则查看贡献者协议中提到的[方法](https://www.secondstate.io/articles/dco/)进行修复

2. 通过[pylint](https://pypi.org/project/pylint/)、[flake8](https://pypi.org/project/flake8/)工具对代码进行静态检查并保证通过，工具安装如下：

   ```
   pip install pylint flake8
   ```

3. 通过[pytest](https://pypi.org/project/pytest/)工具对编写的unittest进行测试并保证运行通过，工具安装如下：

   ```
   pip install pytest
   ```

4. 使用[bazel build](https://bazel.build/)确保项目编译通过

简单起见，你也可以通过在项目根目录下执行[tox](https://tox.wiki/en/latest/#)命令，来一次性完成2~4项的检查，具体流程如下：

```
pip install tox

cd federated-learning/

tox
```

上面的检查通过后，你就可以提交PR了。



### 贡献者协议

我们采用了[DCO(Developer Certificate of Origin)](https://developercertificate.org/)作为贡献者协议，因此在提交PR前务必对协议的使用有所了解。请参考：

- [DCO如何工作](https://probot.github.io/apps/dco/)
- [如何签署DCO](https://www.secondstate.io/articles/dco/)

尤其需要注意的是，必须在每一次的提交上进行sign-off，否则整个PR将不被接受。sign-off作为commit message中的一部分（单独一行），格式如下：

```
Signed-off-by: Full Name <email>
```

