// (C) Copyright 2017 Hewlett Packard Enterprise Development LP.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
// implied.
// See the License for the specific language governing permissions and
// limitations under the License.

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
