// Package config loads gateway configuration from the environment.
package config

import "os"

// Config holds the gateway's runtime configuration.
type Config struct {
	Port              string
	MediaMTXAPIURL    string // MediaMTX control API, e.g. http://mediamtx:9997
	MediaMTXWebRTCURL string // MediaMTX WebRTC (WHEP) base, e.g. http://mediamtx:8889
	InternalToken     string // shared secret for API -> gateway internal calls
	StreamJWTSecret   string // HMAC secret used to verify playback tokens issued by the API
	AllowedOrigin     string // CORS allow-origin for browser WHEP requests
}

func env(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

// Load reads configuration from the environment with sensible dev defaults.
func Load() Config {
	return Config{
		Port:              env("GATEWAY_PORT", "8080"),
		MediaMTXAPIURL:    env("MEDIAMTX_API_URL", "http://mediamtx:9997"),
		MediaMTXWebRTCURL: env("MEDIAMTX_WEBRTC_URL", "http://mediamtx:8889"),
		InternalToken:     env("INTERNAL_API_TOKEN", "change-me-internal-token"),
		StreamJWTSecret:   env("STREAM_JWT_SECRET", "change-me-stream-secret"),
		AllowedOrigin:     env("GATEWAY_CORS_ORIGIN", "*"),
	}
}
