Developer Notes
===============

Source Control
^^^^^^^^^^^^^^

Cascade is maintained on GitHub at: `Cascade Git Repo`_

Requirements
^^^^^^^^^^^^

- Python 3.6
- see requirements.txt for Python module requirements

**Note:**

- Cascade runs in a Docker_ container, so it is possible to do development / testing / investigation etc. in the Cascade Docker_ container and
  thus avoid the complexity of setting up a compatible development environment manually.  See Development_ below.

.. _Development:

Development Environment
^^^^^^^^^^^^^^^^^^^^^^^
To setup a local Cascade development environment:

- Install Docker_
- Clone the `Cascade Git Repo`_
- cd into the repo: ``cd cascade``
- Build the Docker container: ``./docker_build.sh``
- Start Cascade, in the container, running in http mode on localhost: ``python docker_start.py --local``
- Connect to Cascade by pointing your web browser at ``https://127.0.0.1:5001``

To start a bash shell in the Cascade container:

- Start the container using ``python docker_start.py --bash``

The Docker container is architected such that the Cascade source code and output logs reside *outside* the container (i.e. on the host machine).  The container mounts the root of the Cascade project directory (on the host) as ``/home/cascade`` (inside the container).

Logging
^^^^^^^^
Activity is logged to /log/cascade.eliot.log
Old logs are automatically rolled to cascade.eliot.log.1, .2, .3 etc. , and a limited number of logs are retained. 
Logging is performed using the Eliot library (https://eliot.readthedocs.io). Each line in the log file is a JSON object.  The ``/log`` directory contains a few scripts to parse the logs for human readability:

``tree.py`` uses the ``eliot-tree`` library (https://github.com/jonathanj/eliottree) to render logs into a tree structure; the output is written to a .tree file and dumped to the console.

``messages.py`` extracts user messages from logs to create a dump showing the messages which were shown to the user when tasks were executed.

The eliot log parser scripts require a few Python modules to run.  To add them do:

Install pip (if not present)::

    sudo apt install python-pip

Install modules::

    pip install eliot-tree
    pip install pathlib2
    pip install docopt
    pip install colorama

Server Deployment
-----------------

A usable reference deployment of Cascade is running at TDB.

If you require greater privacy, control, or customization you can deploy your own Cascade server. 

Cascade runs in a Docker container on the server.  Docker is responsible for restarting the container if the Cascade process
exits, or the machine reboots.  Additionally, an nginx container proxy is ueed to manage web connections to the Cascade container. Setting up a server from scratch amounts to:

1. Installing Docker
2. Copying the Cascade codebase on the Server
3. Building and Starting the Cascade and Nginx containers using docker-compose.

These steps are detailed in the subsections below.

Setting the server up to host Cascade
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

At the time of this writing, the reference deployment is running on Ubuntu 16.04.  Cascade would likely run on similar modern distributions.

- Install Docker.  The instructions below follow https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-16-04

  - ``curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -``
  - ``sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable”``
  - ``sudo apt-get update``
  - ``apt-cache policy docker-ce``
  - ``sudo apt-get install -y docker-ce``
  - ``sudo systemctl status docker``
  - ``sudo apt install docker-compose``
  - Add self to docker group (so that you don't have to use ``sudo`` for Docker commands):

    - ``sudo usermod -aG docker ${USER}``
    - ``su - ${USER}``


Copying Cascade to the Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TBD


Starting Cascade on the Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TBD


.. _Python: http://www.python.org/
.. _Docker: https://www.docker.com/
.. _Flask: http://flask.pocoo.org/
.. _Cascade Git Repo: https://github.com/epmoyer/cascade/