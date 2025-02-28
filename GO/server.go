package main

import (
	"fmt"
	"net/http"
)

func main() {
	// Serve static files from the "static" directory
	fs := http.FileServer(http.Dir("./static"))
	http.Handle("/", fs)

	// Start the server on port 8080
	fmt.Println("Server running on http://localhost:8080/")
	http.ListenAndServe(":8080", nil)
}
