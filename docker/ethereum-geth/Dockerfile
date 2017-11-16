FROM golang:1.9-alpine as builder

RUN apk add --no-cache --update git gcc musl-dev linux-headers
RUN go get github.com/coreos/etcd/clientv3 && go get github.com/ethereum/go-ethereum

ADD enode-fetcher.go /go
ADD node-registrator.go /go
RUN go build enode-fetcher.go && go build node-registrator.go

FROM ethereum/client-go:release-1.7

COPY --from=builder /go/enode-fetcher /bin/enode-fetcher
COPY --from=builder /go/node-registrator /bin/node-registrator

COPY geth.sh /

ENTRYPOINT ["/geth.sh"]
CMD ["--help"]