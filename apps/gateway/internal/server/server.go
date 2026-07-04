// Package server wires the gateway's HTTP handlers: health, an internal
// provisioning endpoint, and an authorizing WHEP (WebRTC) reverse proxy.
package server

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/visionops/gateway/internal/config"
	"github.com/visionops/gateway/internal/mediamtx"
	"github.com/visionops/gateway/internal/token"
)

// Server holds gateway dependencies.
type Server struct {
	cfg   config.Config
	mtx   *mediamtx.Client
	httpc *http.Client
}

// New constructs a Server.
func New(cfg config.Config) *Server {
	return &Server{
		cfg:   cfg,
		mtx:   mediamtx.New(cfg.MediaMTXAPIURL),
		httpc: &http.Client{Timeout: 20 * time.Second},
	}
}

// Handler returns the fully-wired HTTP handler.
func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", s.health)
	mux.HandleFunc("POST /internal/provision", s.provision)
	mux.HandleFunc("POST /whep/{path}", s.whepOffer)
	mux.HandleFunc("OPTIONS /whep/{path}", s.preflight)
	mux.HandleFunc("PATCH /whep/{path}/{session}", s.whepResource)
	mux.HandleFunc("DELETE /whep/{path}/{session}", s.whepResource)
	mux.HandleFunc("OPTIONS /whep/{path}/{session}", s.preflight)
	return mux
}

func (s *Server) health(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok", "service": "gateway"})
}

type provisionRequest struct {
	Path   string `json:"path"`
	Source string `json:"source"`
}

func (s *Server) provision(w http.ResponseWriter, r *http.Request) {
	if r.Header.Get("X-Internal-Token") != s.cfg.InternalToken {
		writeJSON(w, http.StatusUnauthorized, map[string]string{"error": "unauthorized"})
		return
	}
	var req provisionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Path == "" || req.Source == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid request"})
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()
	if err := s.mtx.EnsurePath(ctx, req.Path, req.Source); err != nil {
		log.Printf("provision failed for %s: %v", req.Path, err)
		writeJSON(w, http.StatusBadGateway, map[string]string{"error": "provisioning failed"})
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "provisioned", "path": req.Path})
}

// whepOffer authorizes a playback token, then forwards the SDP offer to
// MediaMTX and returns the SDP answer.
func (s *Server) whepOffer(w http.ResponseWriter, r *http.Request) {
	s.cors(w)
	path := r.PathValue("path")

	claims, err := token.Verify(bearer(r), s.cfg.StreamJWTSecret)
	if err != nil || claims.Path != path {
		writeJSON(w, http.StatusUnauthorized, map[string]string{"error": "invalid token"})
		return
	}

	body, _ := io.ReadAll(r.Body)
	target := s.cfg.MediaMTXWebRTCURL + "/" + path + "/whep"
	req, err := http.NewRequestWithContext(r.Context(), http.MethodPost, target, bytes.NewReader(body))
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "proxy error"})
		return
	}
	req.Header.Set("Content-Type", contentTypeOr(r, "application/sdp"))

	resp, err := s.httpc.Do(req)
	if err != nil {
		writeJSON(w, http.StatusBadGateway, map[string]string{"error": "media server unavailable"})
		return
	}
	defer resp.Body.Close()

	if ct := resp.Header.Get("Content-Type"); ct != "" {
		w.Header().Set("Content-Type", ct)
	}
	// Rewrite the WHEP resource Location so cleanup routes back through us,
	// never exposing the internal MediaMTX URL.
	if loc := resp.Header.Get("Location"); loc != "" {
		session := loc[strings.LastIndex(loc, "/")+1:]
		w.Header().Set("Location", "/whep/"+path+"/"+session)
	}
	w.WriteHeader(resp.StatusCode)
	_, _ = io.Copy(w, resp.Body)
}

// whepResource proxies WHEP session operations (ICE / close).
func (s *Server) whepResource(w http.ResponseWriter, r *http.Request) {
	s.cors(w)
	path := r.PathValue("path")
	session := r.PathValue("session")
	target := s.cfg.MediaMTXWebRTCURL + "/" + path + "/whep/" + session

	body, _ := io.ReadAll(r.Body)
	req, err := http.NewRequestWithContext(r.Context(), r.Method, target, bytes.NewReader(body))
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "proxy error"})
		return
	}
	if ct := r.Header.Get("Content-Type"); ct != "" {
		req.Header.Set("Content-Type", ct)
	}
	resp, err := s.httpc.Do(req)
	if err != nil {
		writeJSON(w, http.StatusBadGateway, map[string]string{"error": "media server unavailable"})
		return
	}
	defer resp.Body.Close()
	w.WriteHeader(resp.StatusCode)
	_, _ = io.Copy(w, resp.Body)
}

func (s *Server) preflight(w http.ResponseWriter, _ *http.Request) {
	s.cors(w)
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) cors(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", s.cfg.AllowedOrigin)
	w.Header().Set("Access-Control-Allow-Methods", "POST, PATCH, DELETE, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type")
	w.Header().Set("Access-Control-Expose-Headers", "Location")
}

func bearer(r *http.Request) string {
	if h := r.Header.Get("Authorization"); strings.HasPrefix(h, "Bearer ") {
		return strings.TrimPrefix(h, "Bearer ")
	}
	return r.URL.Query().Get("token")
}

func contentTypeOr(r *http.Request, fallback string) string {
	if ct := r.Header.Get("Content-Type"); ct != "" {
		return ct
	}
	return fallback
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}
