# Description

Chief is a simple web interface to assist deployment of web applications.

# Installation

1. `git clone git://github.com/jbalogh/chief.git; cd chief`
2. `cp settings.py.dist settings.py`
3. Fill in settings. The "script" will be run in 3 stages:
    1. `/usr/bin/commander $script pre_update`
    2. `/usr/bin/commander $script update`
    3. `/usr/bin/commander $script deploy`
4. Hook up chief.app to mod\_wsgi, gunicorn, etc.

# Requirements

* [Commander](https://github.com/oremj/commander)
