FROM node:8.6 as builder

RUN npm install -g grunt-cli
RUN mkdir /tmp/git
RUN cd /tmp/git && git clone https://github.com/karalabe/eth-netstats.git
RUN cd /tmp/git/eth-netstats && npm install
RUN cd /tmp/git/eth-netstats && grunt

FROM node:8.6-alpine

RUN apk add --no-cache ca-certificates
COPY --from=builder /tmp/git/eth-netstats /eth-netstats

WORKDIR /eth-netstats

CMD ["npm", "start"]
