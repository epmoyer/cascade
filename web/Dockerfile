FROM continuumio/anaconda3:4.4.0
ARG user_id
RUN echo "Docker container will access files on host using the current user ID: ${user_id}"
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
RUN useradd -ms /bin/bash docker_user
VOLUME /home/cascade
WORKDIR /home/cascade
USER docker_user
ENTRYPOINT ["python", "-m", "cascade", "-w", "http"]