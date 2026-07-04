// Command gateway is the VisionOps AI media edge: it authorizes browser WebRTC
// (WHEP) playback requests using backend-issued tokens and reverse-proxies them
// to an internal MediaMTX media server. MediaMTX is never exposed directly.
package main

import (
	"log"
	"net/http"

	"github.com/visionops/gateway/internal/config"
	"github.com/visionops/gateway/internal/server"
)

func main() {
	cfg := config.Load()
	srv := server.New(cfg)

	addr := ":" + cfg.Port
	log.Printf("gateway listening on %s (mediamtx api=%s webrtc=%s)",
		addr, cfg.MediaMTXAPIURL, cfg.MediaMTXWebRTCURL)

	httpServer := &http.Server{
		Addr:    addr,
		Handler: srv.Handler(),
	}
	if err := httpServer.ListenAndServe(); err != nil {
		log.Fatalf("gateway stopped: %v", err)
	}
}
