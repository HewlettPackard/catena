package main

import (
	"github.com/coreos/etcd/clientv3"
	"flag"
	"strings"
	"time"
	"fmt"
	"context"
)

func main() {

	etcd := flag.String("etcd-cluster", "http://127.0.0.1:2379", "Comma-separated list of etcd nodes")
	clustername := flag.String("name", "catena", "Chain name for identification")

	flag.Parse()

	cfg := clientv3.Config{
		Endpoints: strings.Split(*etcd, ","),
	}

	c, err := clientv3.New(cfg)
	if err != nil {
		panic(err)
	}
	defer c.Close()

	ctx2, cancel2 := context.WithTimeout(context.Background(), 5*time.Second)
	resp2, err := c.Get(ctx2, "ethereum/" + *clustername+"/enode/", clientv3.WithPrefix())
	cancel2()
	if err != nil {
		panic(err)
	}

	var enodes []string

	for _, ev := range resp2.Kvs {
		enodes = append(enodes, string(ev.Value))
	}

	fmt.Printf(strings.Join(enodes, ","))
}
