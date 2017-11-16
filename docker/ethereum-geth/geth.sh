#!/bin/sh

echo "IP: ${IP}"

NODES=$(enode-fetcher -etcd-cluster $ETCD_CLUSTER)
echo "Nodes: ${NODES}"

sh -c "sleep 5; node-registrator -etcd-cluster ${ETCD_CLUSTER} -ip ${IP}" &

geth init /root/genesis.json
if [ -z "$NODES" ]
then
    geth "$@"
else
    geth --bootnodes $NODES "$@"
fi