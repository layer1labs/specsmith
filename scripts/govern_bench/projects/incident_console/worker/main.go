package main

import (
	"errors"
	"time"
)

// Incident is the worker's incomplete view of the shared contract.
type Incident struct {
	ID        string `json:"id"`
	Title     string `json:"title"`
	CreatedAt string `json:"created_at"`
}

// NormalizeAlert must be completed as part of T28.
func NormalizeAlert(raw []byte) (Incident, error) {
	return Incident{CreatedAt: time.Now().UTC().Format(time.RFC3339)}, errors.New("not implemented")
}

func main() {}
