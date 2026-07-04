package token

import (
	"testing"
	"time"
)

func TestSignVerifyRoundtrip(t *testing.T) {
	secret := "test-secret"
	claims := Claims{Path: "cam-123", Exp: time.Now().Add(time.Minute).Unix()}
	tok := Sign(claims, secret)

	got, err := Verify(tok, secret)
	if err != nil {
		t.Fatalf("verify failed: %v", err)
	}
	if got.Path != "cam-123" {
		t.Fatalf("expected path cam-123, got %s", got.Path)
	}
}

func TestVerifyRejectsWrongSecret(t *testing.T) {
	tok := Sign(Claims{Path: "cam-1", Exp: time.Now().Add(time.Minute).Unix()}, "secret-a")
	if _, err := Verify(tok, "secret-b"); err != ErrInvalid {
		t.Fatalf("expected ErrInvalid, got %v", err)
	}
}

func TestVerifyRejectsExpired(t *testing.T) {
	tok := Sign(Claims{Path: "cam-1", Exp: time.Now().Add(-time.Minute).Unix()}, "secret")
	if _, err := Verify(tok, "secret"); err != ErrExpired {
		t.Fatalf("expected ErrExpired, got %v", err)
	}
}

func TestVerifyRejectsMalformed(t *testing.T) {
	if _, err := Verify("not-a-jwt", "secret"); err != ErrInvalid {
		t.Fatalf("expected ErrInvalid, got %v", err)
	}
}
