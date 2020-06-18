# DPOP
![PyPI - Python Version](https://img.shields.io/badge/python-≥3-blue.svg)

##Dependency
```yaml
pip install numpy
pip install pandas
pip install 
```

## Running the program
```sh
sh test.sh
```


## Send and receive message
send message function is in agent\
receive message function is in communication.listen_func


## New functions
now use the properties YAML files
```yaml
agent_mode: default/list/split/pipeline
comp_speed: 100
net_speed: 100
network_customization: False
slow_processing: False
network_protocol: UDP_FEC
```
can be edited by using properties.py

network_customization, slow_processing are boolean. If set to False, means there is no need 
comp_speed, net_speed do not taken into running.


## To-Do-List
    