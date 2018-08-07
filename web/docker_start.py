#!/usr/bin/env python
""" Run the 'cascade' docker container in interactive mode, starting the default app (cascade webserver) in the container.
"""
import sys
import os
import subprocess
import argparse

if __name__ == "__main__":

    # Process command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--local", help="Map Cascade webserver onto localhost (127.0.0.1)",
                    action="store_true")
    parser.add_argument("-a", "--always", help="Always restart the container if it stops",
                    action="store_true")
    parser.add_argument("-b", "--bash", help="Start a bash shell in the container",
                    action="store_true")
    args = parser.parse_args()

    if args.always and args.bash:
        print("--always and --bash are mutually exclusive. Pick a side! Aborting.")
        sys.exit()

    # If localhost was specified on the command line, then map the Cascade webserver in
    # the container to this machine's localhost interface, otherwise host it 
    # publicly on 0.0.0.0
    #
    if args.local:
        ip_address = '127.0.0.1'
        print('Cascade webserver will be mapped to localhost (127.0.0.1)')
    else:
        ip_address = '0.0.0.0'
        print('Cascade webserver will be hosted publicly (0.0.0.0).  To use localhost instead, start using "docker_start.py --local".')

    working_directory = os.getcwd()
    if not os.path.isfile(os.path.join(working_directory, 'cascade', '__main__.py')):
        print('ABORTED: You must run this script from the root cascade directory (the root of the git repo).')
        sys.exit()

    docker_options = '-p {}:5001:5001'.format(ip_address)
    docker_options += ' -v "{}":/home/cascade'.format(working_directory)
    if args.always:
        docker_options += ' --restart always --detach'
    else:
        docker_options += ' -ti --restart no'

    if args.bash:
        docker_options += ' --entrypoint "/bin/bash"'

    command = 'docker run ' + docker_options + ' cascade'
    print(command)
    subprocess.call(command, shell=True)
