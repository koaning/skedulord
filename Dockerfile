FROM python:3.6

COPY . .

RUN python setup.py install

RUN pytest
