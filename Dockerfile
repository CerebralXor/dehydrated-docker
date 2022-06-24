FROM python:3.10
WORKDIR /usr/src/app

ADD requirements.txt .
RUN pip install --no-cache -r requirements.txt
RUN git clone --depth=1 https://github.com/dehydrated-io/dehydrated.git
RUN rm -rf ./dehydrated/{.git,docs}
ENV PATH="/usr/src/app/dehydrated:${PATH}"
ENV TLDEXTRACT_CACHE=/tmp/tldextract.cache

ADD hooks.sh .
ADD config /etc/dehydrated/
ADD start.py /usr/src/app/dehydrated
ADD update_swarm_secrets.py .

CMD start.py -c
