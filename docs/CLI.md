

## CLI TOOL

### Usage

We provide a CLI tool that can help you use the federated learning services more conveniently. You can use it to manage your federated jobs and models. Below is how to use the CLI tools.

**step one**: install

```
pip install nsfl-ctl
```

**step two**: config service address

```
nsfl-ctl set config -s 127.0.0.1:8080
nsfl-ctl set config -d 127.0.0.1:8081
nsfl-ctl set config -u Bob
nsfl-ctl set config -p ******
```

**step three**: execute command

```
nsfl-ctl create job default -f /path/job.json -m /path/model.h5
```

### Commands

Now you know how to use command line tool, here is the list of commands supported by CLI.

Global

- health
- set config
- get config

Job Manage

- create job

- delete job

- get job

- get jobs

- get namespace

- start job

- stop job

- update job


Model Manage

- create model 
- delete model
- download model
- get models 
- get model

If you want to know more details about how to use these commands, please try `nsfl-ctl --help` to learn more.

