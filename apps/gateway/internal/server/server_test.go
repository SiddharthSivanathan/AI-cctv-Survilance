package server

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/visionops/gateway/internal/config"
	"github.com/visionops/gateway/internal/token"
)

func testServer() *Server {
	return New(config.Config{
		MediaMTXAPIURL:    "http://mediamtx:9997",
		MediaMTXWebRTCURL: "http://mediamtx:8889",
		InternalToken:     "internal",
		StreamJWTSecret:   "secret",
		AllowedOrigin:     "*",
	})
}

func TestHealth(t *testing.T) {
	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	testServer().Handler().ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}
}

func TestProvisionRequiresInternalToken(t *testing.T) {
	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodPost, "/internal/provision", nil)
	testServer().Handler().ServeHTTP(rec, req)
	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", rec.Code)
	}
}

func TestWhepRejectsInvalidToken(t *testing.T) {
	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodPost, "/whep/cam-1", nil)
	req.Header.Set("Authorization", "Bearer bogus")
	testServer().Handler().ServeHTTP(rec, req)
	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", rec.Code)
	}
}

func TestWhepRejectsTokenForDifferentPath(t *testing.T) {
	tok := token.Sign(token.Claims{Path: "cam-2", Exp: time.Now().Add(time.Minute).Unix()}, "secret")
	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodPost, "/whep/cam-1", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	testServer().Handler().ServeHTTP(rec, req)
	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 for path mismatch, got %d", rec.Code)
	}
}
