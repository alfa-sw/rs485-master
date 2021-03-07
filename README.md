# rs485 Master

a simple aplication using a frontend UI on a browser aimed to check communication on a rs485 field bus.

## Installation

1. create a virtualenv 
>     $ export VIRTENV_ROOT=desired-virtenv_root-path
>     $ mkdir ${VIRTENV_ROOT}
>     $ virtualenv -p /usr/bin/python3 ${VIRTENV_ROOT}

2. clone this project in ${PROJECT_ROOT}
>     $ git clone git@github.com:alfa-sw/rs485-master.git

3. build Install in edit mode:
>     $ . ${VIRTENV_ROOT}/bin/activate
>     $ cd ${PROJECT_ROOT}
>     $ pip install -e ./

4. Run:
>     $ (. ${VIRTENV_ROOT}/bin/activate ; rs485_master &)
>     $ chromium http://127.0.0.1:8000/ &
>     $ firefox http://127.0.0.1:8000/ &


## Communication between browser and backend

Data between browser and backend is exchanged using websocket.

Any request to the backend is a JSON object with the following schema:

```
 {
    "command_name": <command_name>
    "arguments": <arguments>
 }
```

where <command_name> is an identificator of the request to the backend,
and <arguments> is a JSON object whose schema variable from a command to another.

The frontend response to a request with the following JSON schema:

```
{
    "answer": <command_name>
    "content": <answer_content>
}
```
where <answer_content> contains a boolean value or a JSON object.

When the frontend wants to send data asyncronously the following schema is used:
```
{
    "signal": <signal_name>
    "content": <signal_content>
}
```

## Principle of operation

When a new websocket is opened, a new instance of Tornado's WebsockHandler is created.
During initialization an instance of rs485_Master is created (see source documentation for details.)
The callback to send a "signal object" is setup also.
Any request is routed to a method of the rs485_Master instance, and the return value is
packed into the answer object. 
