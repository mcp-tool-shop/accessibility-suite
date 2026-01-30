# Why prov-spec exists

## The problem

Provenance is everywhere. Every pipeline, every tool, every system generates some form of "where did this come from?" metadata. Build systems track inputs. ML pipelines record hyperparameters. Data workflows log transformations.

But it's informal, implicit, unverifiable. Strings without contracts. Field names that vary by vendor. Hashes computed over undefined bytes. Claims you can't check without running the original system. This doesn't scale. When provenance is tied to a specific tool, it dies with that tool.

## What went wrong historically

Provenance has been tied to:

- **Frameworks** — you need the framework to verify the provenance
- **SDKs** — you need the SDK to parse the records
- **Vendors** — you need the vendor's system to trust the claims

This creates a problem: verification becomes impossible without "the original system." If your audit happens five years later, or in a different language, or after the vendor pivots — you're stuck.

The result is that most provenance is write-only. Systems generate it, but nothing consumes it reliably. It exists for compliance theater, not actual verification.

## The core idea

**Provenance should be verifiable without trusting the producer.**

That's the thesis. Everything in prov-spec hangs off this single requirement.

If I can't verify your provenance claim using only:
- the record you gave me
- a specification I can read
- inputs I can obtain

...then your provenance is not provenance. It's a story.

## What prov-spec standardizes

- **Method identity** — stable, namespaced IDs that mean the same thing everywhere
- **Semantics** — what a method ID *commits to* when claimed
- **Canonical bytes** — exactly what gets hashed, no ambiguity
- **Validation behavior** — test vectors that define correct output

## What prov-spec refuses to standardize

- **Storage** — where you keep records is your problem
- **Transport** — how you send records is your problem
- **UI** — how you display records is your problem
- **Policy** — who trusts what is your problem

This restraint is a feature. Every additional thing a spec standardizes is another thing that can break, another thing that creates lock-in, another thing that prevents adoption.

prov-spec is deliberately minimal. It standardizes the verification surface and nothing else.

## Why method IDs are the unit of interoperability

A method ID like `integrity.digest.sha256` is not a function call. It's a *contract*.

When a provenance record claims `integrity.digest.sha256`, it's saying:

> "I computed a SHA-256 hash. The hash is over canonical JSON bytes. The bytes were computed using the canonicalization rules in the spec. The hex is lowercase. You can verify this yourself."

That contract survives:
- Rewrites of the producing system
- Ports to different languages
- Years of bit-rot
- Changes in organizational ownership

Method IDs are portable truth. Combined with test vectors, they become *executable* portable truth.

## What success looks like

Multiple engines, different languages, same vectors, same answers.

A Python tool produces a provenance record. A Rust verifier checks it. A Node.js dashboard displays it. A Go auditor validates the chain. None of them share code. All of them agree on what the record means.

That's the goal. Not "everyone uses our SDK." Not "everyone adopts our framework." Just: everyone agrees on what the words mean, and can prove it.

## Non-goals

prov-spec is **not a framework**. There's no runtime, no library you must import, no service you must call.

prov-spec is **not a governance body**. We don't certify implementations, don't issue compliance badges, don't arbitrate disputes.

prov-spec is **not an endorsement mechanism**. A valid provenance record doesn't mean the content is good, true, or trustworthy. It means the record is well-formed and the claims are verifiable.

## Closing

prov-spec exists so provenance can outlive the systems that generate it.
