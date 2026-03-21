# Security Policy

## Supported Versions

| Version   | Supported |
|-----------|-----------|
| 5.0.x     | ✅         |
| < 5.0     | ❌ (legacy PowerShell — deprecated) |

## Security Measures

This installer implements the following security practices:

- **No shell injection** — All subprocess calls use explicit argument lists (`subprocess.run` with `shell=False`)
- **SHA-256 verification** — Downloaded files are verified against checksums when available
- **Zip slip prevention** — Archive extraction validates that all paths remain within the target directory
- **HTTPS only** — All download URLs use HTTPS
- **Default local binding** — ComfyUI listens on `127.0.0.1` by default, not `0.0.0.0`
- **No mutable global state** — Configuration is passed explicitly, not via global variables
- **CI audits** — Bandit (SAST) and pip-audit run on every push via GitHub Actions
- **Pickle model scanner** — `picklescan`-based detection of malicious code in `.ckpt`/`.pt`/`.pth` model files. Auto-runs during updates, available as `scan-models` CLI command.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT open a public issue**
2. Email: **security@umeairt.com** (or use GitHub's private vulnerability reporting)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
4. You will receive a response within **48 hours**

## Scope

This policy covers:
- The installer itself (`src/`)
- Bootstrap scripts (`Install.bat`, `Install.sh`)
- Configuration files (`scripts/*.json`)

It does **not** cover:
- ComfyUI core (report to [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI))
- Third-party custom nodes
- Pre-built wheel files hosted externally
