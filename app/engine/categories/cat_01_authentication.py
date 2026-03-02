from app.engine.categories.base import BaseCategoryAnalyzer


class Cat01AuthenticationAnalyzer(BaseCategoryAnalyzer):
    category_id = 1
    name = "Authentication & Identity"
    part = "A"
    min_signals = 25

    def get_checklist(self) -> list[str]:
        return [
            "Audit login flow: validate credential verification, rate limiting, and error handling",
            "Audit signup flow: validate email verification, CAPTCHA, and duplicate prevention",
            "Audit password reset: validate token entropy, expiry, single-use, and secure delivery",
            "Audit MFA implementation: TOTP/HOTP, backup codes, and fallback paths",
            "Audit SSO integration: validate IdP configuration and trust boundaries",
            "Audit SAML flow: validate assertion signing, audience restriction, and replay protection",
            "Audit OAuth2 flow: validate authorization code, PKCE, and redirect URI validation",
            "Audit OIDC flow: validate ID token verification, nonce, and audience claims",
            "Audit session lifecycle: creation, renewal, invalidation, and timeout enforcement",
            "Audit JWT security: algorithm enforcement, signature verification, expiry validation",
            "Audit API key lifecycle: creation, rotation, revocation, and scope binding",
            "Audit service-to-service auth: mTLS, JWT, or OAuth2 client credentials",
            "Audit credential storage: bcrypt/argon2id for passwords, no plaintext",
            "Audit account enumeration: identical error messages and timing for valid/invalid users",
            "Audit brute force protection: lockout, CAPTCHA, and progressive delays",
            "Audit session fixation: regenerate session ID on privilege change",
            "Audit session hijacking: HttpOnly, Secure, SameSite cookie flags",
            "Audit token leakage vectors: Referer, logs, error messages, client storage",
            "Audit multi-tenancy auth isolation: tenant context in all auth decisions",
            "Audit privileged access management: PAM, just-in-time access, approval workflows",
            "Audit password policy: NIST 800-63 compliance, length, complexity, history",
            "Audit remember-me/persistent sessions: secure token, limited scope, revocation",
            "Audit account recovery/takeover: identity verification and secure handoff",
            "Audit OAuth misconfiguration: open redirect, scope creep, token leakage",
            "Audit SAML security: XML signature wrapping, assertion injection",
            "Audit WebAuthn/FIDO2: attestation, user verification, credential binding",
            "Audit certificate-based auth: chain validation, revocation checking",
            "Audit SSO logout propagation: front-channel, back-channel, session termination",
            "Audit credential rotation automation: scheduled rotation, grace period",
            "Audit default credentials: no hardcoded admin/test passwords in codebase",
            "Audit password reset token security: cryptographically random, short TTL",
            "Audit auth header forwarding in proxy chains: strip or sanitize before backend",
        ]
