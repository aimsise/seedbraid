# Helix v2 Threat Model

## Assets
- Source file content represented by chunk references and optional RAW payloads.
- Genome database containing reusable chunk bytes.
- Seed metadata (manifest) including file hashes and chunking parameters.

## Adversary Capabilities
- Observes published seed bytes (e.g., on IPFS).
- Performs dictionary attacks on known files/chunks.
- Tampering attempts against seed bytes.

## Key Risks
1. Content inference from hashes
- Chunk hashes can reveal known plaintext via precomputed dictionaries.

2. Metadata leakage
- Manifest exposes source size, hash, and chunking parameters.

3. Portable mode leakage
- RAW payloads can expose full unknown content directly.

4. Tampering
- Modified container sections could induce corruption if unchecked.

## Current Mitigations
- Integrity section validates manifest, recipe, and full payload CRC32.
- Verify/decode enforce expected output SHA-256.
- Portable mode is opt-in and defaults off.

## Limitations
- CRC32 detects accidental corruption and simple tampering, not cryptographic forgery.
- No built-in encryption or access control in v2.
- IPFS content addressing is public-by-default once CID is shared.

## Recommended Operational Controls
- Prefer non-portable seeds for sensitive data when receiver has trusted genome.
- Encrypt seed before publication when confidentiality is needed.
- Avoid publishing sensitive manifests; use wrapper metadata encryption.
- Pin only from trusted nodes and maintain local audit logs.

## Encryption Option Policy (Future)
- Add optional envelope encryption section:
  - AEAD-encrypted payload sections
  - key wrapping via recipient public key(s)
- Keep manifest split into public/private parts to reduce metadata leakage.
