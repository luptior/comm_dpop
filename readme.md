# DPOP
![PyPI - Python Version](https://img.shields.io/badge/python-≥3-blue.svg)


## Running the program
```sh
sh test.sh
```


## Send and receive message
send message function is in agent\
receive message function is in communication.listen_func


## New functions
1, choose different types of connection speed(under construction in network)\
```python
net_speed = 100
```
2, choose different computation speed
```python
computation_speed = 30
```
3, split processing\
split the message into mutiple small packages then send


## To-Do-List
1, working on the ability to process msg by parts\
2, Pipeline Structure\
    Since we can spend package in small parts, we  are able to do pipeline
    