# Helix Packaging and Pricing Draft (v0)

This draft defines an OSS-first product boundary with optional paid layers.

## Positioning
- Core value: lossless, reference-based reconstruction with CDC and portable seed transport.
- OSS principle: core data format, codec, and local operations remain open.
- Paid principle: monetize operational complexity, governance, and managed reliability.

## Target Segments
1. Engineering teams managing large binary artifacts.
2. ML/data teams distributing frequently updated model/data bundles.
3. Platform teams requiring reproducible integrity and operational controls.

## Packaging Model
### OSS (Free)
- CLI and format:
  - `encode`, `decode`, `verify`, `prime`
  - `publish`, `fetch`, `pin-health`, `doctor`
- HLX1/HLE1 specs and compatibility fixtures.
- Local genome operations and benchmark tooling.
- Community support (GitHub issues/discussions).

### Team Cloud (Paid)
- Hosted control plane:
  - CID registry workspace
  - project/member management
  - usage dashboard (seed count, egress estimate, restore stats)
- Convenience/security:
  - managed key storage integration
  - policy templates for publish/verify flows
- Support:
  - business-hours support SLA

### Enterprise (Paid)
- Governance/security:
  - SSO/SAML
  - RBAC and approval workflows
  - immutable audit logs/export
- Reliability/operations:
  - managed pinning policy and retention controls
  - compliance reporting
  - private deployment options
- Support:
  - priority SLA and onboarding package

## Feature Matrix (Draft)
| Capability | OSS | Team Cloud | Enterprise |
|---|---|---|---|
| HLX1 encode/decode/verify | Yes | Yes | Yes |
| CDC + dedup benchmark tooling | Yes | Yes | Yes |
| IPFS publish/fetch CLI | Yes | Yes | Yes |
| Hosted registry/workspace | No | Yes | Yes |
| Team access controls | No | Basic | Advanced (SSO/RBAC) |
| Audit logs | Local only | 30-day | Long-term + export |
| Managed pin/policy controls | No | Optional | Full |
| Support SLA | Community | Business-hours | Priority/contract |

## Pricing Draft (USD)
Assumptions:
- Initial target is developer-led adoption with low friction.
- Pricing is validated through pilot conversions, not fixed yet.

Suggested starting bands:
1. Team Cloud
- $49/month per workspace (includes small usage baseline).
- Optional usage overage by stored/pinned GB and transfer GB.

2. Enterprise
- $1,500 to $5,000/month base contract depending on:
  - user count
  - required SLA
  - deployment model (shared vs private)

Notes:
- Keep OSS unrestricted for local workflows to preserve adoption flywheel.
- Monetize controls and managed operations, not core format access.

## GTM Hypotheses and Validation
Primary GTM hypotheses:
1. Teams adopt OSS first, then upgrade for governance and reliability.
2. Security/compliance and auditability are strongest paid conversion drivers.
3. Registry + policy workflow creates recurring operational value.

Validation plan:
1. Run 5-10 pilot teams over 6-8 weeks.
2. Track conversion signals:
  - weekly active projects
  - restore success rates
  - publish/fetch volume
  - security feature requests
3. Adjust pricing bands after pilot willingness-to-pay interviews.

## Launch Sequence (Draft)
1. OSS maturity gate
- keep compatibility and benchmark gates green
- stabilize operator runbooks

2. Team Cloud alpha
- registry + workspace + basic analytics
- limited design partners

3. Enterprise package
- SSO/RBAC/audit + support contracts
- compliance-ready sales motion
