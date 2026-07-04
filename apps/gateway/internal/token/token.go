// Package token verifies (and, for tests, signs) the short-lived HS256
// playback tokens issued by the FastAPI control plane.
package token

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"strings"
	"time"
)

// Claims are the playback-token claims the gateway cares about.
type Claims struct {
	Path string `json:"path"` // camera id / MediaMTX path this token authorizes
	Exp  int64  `json:"exp"`  // expiry (unix seconds)
}

var (
	// ErrInvalid is returned for any malformed or tampered token.
	ErrInvalid = errors.New("invalid token")
	// ErrExpired is returned when a token is past its expiry.
	ErrExpired = errors.New("token expired")
)

func b64(data []byte) string {
	return base64.RawURLEncoding.EncodeToString(data)
}

// Verify checks an HS256 JWT signature and expiry, returning its claims.
func Verify(tokenString, secret string) (Claims, error) {
	var claims Claims
	parts := strings.Split(tokenString, ".")
	if len(parts) != 3 {
		return claims, ErrInvalid
	}

	signingInput := parts[0] + "." + parts[1]
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write([]byte(signingInput))
	expected := mac.Sum(nil)

	got, err := base64.RawURLEncoding.DecodeString(parts[2])
	if err != nil || !hmac.Equal(expected, got) {
		return claims, ErrInvalid
	}

	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return claims, ErrInvalid
	}
	if err := json.Unmarshal(payload, &claims); err != nil {
		return claims, ErrInvalid
	}
	if claims.Exp > 0 && time.Now().Unix() > claims.Exp {
		return claims, ErrExpired
	}
	return claims, nil
}

// Sign produces an HS256 JWT for the given claims. Used by tests; the API is
// the real issuer in production.
func Sign(claims Claims, secret string) string {
	header := b64([]byte(`{"alg":"HS256","typ":"JWT"}`))
	payload, _ := json.Marshal(claims)
	signingInput := header + "." + b64(payload)
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write([]byte(signingInput))
	return signingInput + "." + b64(mac.Sum(nil))
}
