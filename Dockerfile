FROM fnndsc/ubuntu-python3


RUN apt-get update;
RUN apt-get install -y python3 virtualenv virtualenv-clone virtualenvwrapper wget make gcc supervisor;

RUN mkdir -p /code
ADD ./ /code

WORKDIR /code
RUN pip install -r requirements.txt
