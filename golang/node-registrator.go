package main

import (
	"github.com/coreos/etcd/clientv3"
	"context"
	"time"
	"fmt"
	"flag"
	"strings"
	"github.com/ethereum/go-ethereum/p2p/discover"
	"github.com/ethereum/go-ethereum/crypto"
	"os"
	"net"
)

func retrieveEnodeId(nodekey string) (string) {
	key, err := crypto.LoadECDSA(nodekey)
	if err != nil {
		panic(err)
	}
	return discover.PubkeyID(&key.PublicKey).String()
}

func main() {

	etcd := flag.String("etcd-cluster", "http://127.0.0.1:2379", "Comma-separated list of etcd nodes")
	clustername := flag.String("name", "catena", "Chain name for identification")
	ipAddress := flag.String("ip", "127.0.0.1", "Node IP Address")
	port := flag.Int("port", 30303, "Node Port")

	nodekeyFile := flag.String("nodekey", "/root/.ethereum/geth/nodekey", "Location of nodekey")
	gethIpc := flag.String("ipc", "/root/.ethereum/geth.ipc", "Geth IPC location")

	ttl := flag.Int("ttl", 20, "TTL for entry in seconds")
	interval := flag.Int("interval", 5, "Check interval in seconds")

	flag.Parse()

	cfg := clientv3.Config{
		Endpoints: strings.Split(*etcd, ","),
	}

	c, err := clientv3.New(cfg)
	if err != nil {
		panic(err)
	}
	defer c.Close()

	// Granting Lease for 15 seconds (TTL for our entries)
	grantedLease, err := c.Grant(context.Background(), (int64)(*ttl))
	if err != nil {
		panic(err)
	}

	enode := fmt.Sprintf("enode://%s@%s:%d", retrieveEnodeId(*nodekeyFile), *ipAddress, *port)
	hostname, err := os.Hostname()
	if err != nil {
		panic(err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	_, err = c.Put(ctx, fmt.Sprintf("ethereum/%s/enode/%s", *clustername, hostname), enode, clientv3.WithLease(grantedLease.ID))
	cancel()
	if err != nil {
		panic(err)
	}

	for true {
		time.Sleep(time.Second * time.Duration(*interval))
		socket, err := net.Dial("unix", *gethIpc)
		if err == nil {
			socket.Close()
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			_, keepaliveError := c.KeepAliveOnce(ctx, grantedLease.ID)
			cancel()
			if keepaliveError != nil {
				panic(keepaliveError)
				return
			}
		} else {
			return
		}
	}
}
