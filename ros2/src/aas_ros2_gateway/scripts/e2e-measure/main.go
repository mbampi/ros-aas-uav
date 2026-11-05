package main

import (
	"e2e-measure/proxy"
	"flag"
	"fmt"
	"os"
)

func main() {
	mode := flag.String("mode", "in", "Mode to run: 'in' for in-proxy, 'out' for out-proxy")
	flag.Parse()

	switch *mode {
	case "in":
		if err := proxy.RunInProxy(); err != nil {
			fmt.Fprintf(os.Stderr, "in-proxy error: %v\n", err)
			os.Exit(1)
		}
	case "out":
		// if err := proxy.RunOutProxy(); err != nil {
		// 	fmt.Fprintf(os.Stderr, "out-proxy error: %v\n", err)
		// 	os.Exit(1)
		// }
	default:
		fmt.Fprintf(os.Stderr, "unknown mode: %s\n", *mode)
		os.Exit(2)
	}
}
