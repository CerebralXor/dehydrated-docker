FROM python:3.10
WORKDIR /usr/src/app

RUN pip install --no-cache dns-lexicon[full]
RUN git clone --depth=1 https://github.com/dehydrated-io/dehydrated.git
RUN rm -rf ./dehydrated/{.git,docs}
ENV PATH="/usr/src/app/dehydrated:${PATH}"
ENV TLDEXTRACT_CACHE=/tmp/tldextract.cache

ADD hooks.sh .
ADD config /etc/dehydrated/
ADD start.py /usr/src/app/dehydrated

CMD start.py -c
