// Package mediamtx is a minimal client for the MediaMTX control API used to
// provision on-demand RTSP source paths.
package mediamtx

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// Client talks to the MediaMTX control API.
type Client struct {
	apiURL string
	http   *http.Client
}

// New returns a MediaMTX client for the given control API base URL.
func New(apiURL string) *Client {
	return &Client{apiURL: apiURL, http: &http.Client{Timeout: 10 * time.Second}}
}

type pathConfig struct {
	Source         string `json:"source"`
	SourceOnDemand bool   `json:"sourceOnDemand"`
}

// EnsurePath creates (or updates) an on-demand path that pulls from the given
// RTSP source. MediaMTX only connects to the source when a reader is present.
func (c *Client) EnsurePath(ctx context.Context, name, source string) error {
	body, _ := json.Marshal(pathConfig{Source: source, SourceOnDemand: true})

	// Try to add; if it already exists, patch it instead.
	addURL := fmt.Sprintf("%s/v3/config/paths/add/%s", c.apiURL, name)
	if err := c.do(ctx, http.MethodPost, addURL, body); err == nil {
		return nil
	}
	patchURL := fmt.Sprintf("%s/v3/config/paths/patch/%s", c.apiURL, name)
	return c.do(ctx, http.MethodPatch, patchURL, body)
}

// DeletePath removes a provisioned path.
func (c *Client) DeletePath(ctx context.Context, name string) error {
	delURL := fmt.Sprintf("%s/v3/config/paths/delete/%s", c.apiURL, name)
	return c.do(ctx, http.MethodDelete, delURL, nil)
}

func (c *Client) do(ctx context.Context, method, url string, body []byte) error {
	var reader *bytes.Reader
	if body != nil {
		reader = bytes.NewReader(body)
	} else {
		reader = bytes.NewReader(nil)
	}
	req, err := http.NewRequestWithContext(ctx, method, url, reader)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return fmt.Errorf("mediamtx %s %s: status %d", method, url, resp.StatusCode)
	}
	return nil
}
