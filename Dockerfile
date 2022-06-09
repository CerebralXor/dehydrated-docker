FROM python:3.9
WORKDIR /usr/src/app

RUN pip install --no-cache dns-lexicon[full]
RUN git clone https://github.com/dehydrated-io/dehydrated.git
ENV PATH="/usr/src/app/dehydrated:${PATH}"
ENV TLDEXTRACT_CACHE=/tmp/tldextract.cache

ADD hooks.sh .
ADD config /etc/dehydrated/
ADD start.py /usr/src/app/dehydrated

CMD start.py -c
