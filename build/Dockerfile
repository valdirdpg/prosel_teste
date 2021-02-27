FROM python:3.7.4
ENV PYTHONUNBUFFERED 1
RUN mkdir /app
WORKDIR /app
ADD .netrc /root/.netrc
ADD requirements.txt /app/
RUN pip install -U setuptools
RUN pip install -U pip
RUN pip install -r requirements.txt
ADD . /app/
COPY build/rancher/settings.py /app/portaldocandidato/
EXPOSE 8000
COPY build/rancher/run.sh /app/
CMD ./run.sh
