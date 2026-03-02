from app.engine.categories.base import BaseCategoryAnalyzer


class Cat05CryptographyAnalyzer(BaseCategoryAnalyzer):
    category_id = 5
    name = "Cryptography & Key Management"
    part = "A"
    min_signals = 15

    def get_checklist(self) -> list[str]:
        return [
            "Audit weak hash algorithms: no MD5, SHA1 for security; use SHA-256+ or Argon2",
            "Audit weak encryption algorithms: no DES, 3DES, RC4; use AES-256-GCM",
            "Audit insufficient key length: RSA 2048+ min, ECDH P-256+, AES 128+",
            "Audit bad RNG: use os.urandom, secrets module; no random.random for crypto",
            "Audit hardcoded keys/IVs: keys from KMS, env, or secure config only",
            "Audit IV/nonce reuse: unique IV per encryption with same key",
            "Audit missing encryption authentication: use AEAD (GCM, ChaCha20-Poly1305)",
            "Audit TLS configuration: 1.2+ only, strong ciphers, no SSLv3/TLS 1.0",
            "Audit certificate chain validation: full chain verification, no skip",
            "Audit certificate expiry monitoring: alert before expiry, automated renewal",
            "Audit certificate pinning: pin public key for mobile/sensitive clients",
            "Audit HSTS: Strict-Transport-Security header with appropriate max-age",
            "Audit timing side-channel: constant-time comparison for secrets/tokens",
            "Audit key derivation: PBKDF2/Argon2 with sufficient iterations for passwords",
            "Audit downgrade attacks: TLS version and cipher negotiation protection",
            "Audit digital signature verification: verify before trust, algorithm enforcement",
            "Audit certificate transparency: CT logs for issued certs",
            "Audit entropy sources: /dev/urandom, CSPRNG for key generation",
        ]
