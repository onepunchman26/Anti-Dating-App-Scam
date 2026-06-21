# Verifiable Reports

AI-SlowMatch risk reports are local JSON documents that should validate against:

```text
src/anti_dating_scam/schemas/risk_report.schema.json
```

## MVP Integrity Flow

1. Generate report JSON.
2. Validate against JSON Schema.
3. Canonicalize JSON deterministically.
4. Compute SHA-256 hash.
5. Attach a local hash-based signature block.
6. Verify whether content changed after signing.

## Important Limitation

The MVP signing layer is hash-based integrity metadata, not a complete cryptographic identity system.

Required disclaimer:

> A valid report signature only means the report file was not modified after signing and conforms to the project schema. It does not prove that the submitted conversation is authentic or that any real person committed wrongdoing.

## Future Work

- Real local keypair generation.
- Trust store for known signers.
- Optional notary service that signs only hashes.
- Rust/Tauri signing and verification layer.
