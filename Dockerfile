# Use an official Python runtime as a parent image
FROM python:3.8.5

RUN mkdir /Hermes

WORKDIR /Hermes

COPY . /Hermes

RUN pip install -r requirements.txt

WORKDIR /Hermes/webwhatsapi

RUN pip install -r requirements.txt

RUN pip install ./

WORKDIR /Hermes

ENV SELENIUM "http://firefox:4444/wd/hub"
