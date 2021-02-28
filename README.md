# rs485 Master

a simple aplication using a frontend UI on a browser aimed to check communication on a rs485 field bus.

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
>     $ (. ${VIRTENV_ROOT}/bin/activate ; pyjamapeolple &)
>     $ chromium http://127.0.0.1:8000/ &
>     $ firefox http://127.0.0.1:8000/ &



