---
simd: '0530'
title: BLS Aggregate Signature Verification for Alpenglow VotePackets
authors:
  - Richard Patterson <@De-ASI-INTERFACE>
category: Standard
type: Core
status: Draft
created: 2026-06-26
feature: (fill in with feature key and github tracking issue once accepted)
depends-on:
  - '0326'
  - '0387'
  - '0388'
---

## Summary

SIMD-0326 (Alpenglow) introduced `VotePacket` as the unit of gossip-free
voting between validators. However, the `signature_set` field carried inside
every `VotePacket` is currently accepted by the Votor pipeline without any
cryptographic verification of the underlying BLS12-381 aggregate signature.
This SIMD closes that gap by specifying the mandatory verification algorithm,
its feature-gate lifecycle, its compute-budget accounting, and the exact
error variants that must cause a `VotePacket` to be silently dropped.


## Motivation

A `VotePacket` that carries an unverified `signature_set` allows any network
participant to inject malformed or entirely forged vote data into the Votor
pipeline at zero cryptographic cost. The consequences are:

1. **Stake inflation**: A Byzantine node may contribute fake notarize/skip
   votes that are counted toward certificate thresholds without holding the
   claimed stake.
2. **Certificate forgery**: Without verification, a single packet with
   fabricated aggregated pubkeys could falsely advance a slot to
   fast-finalization or slow-finalization status.
3. **DoS amplification**: Each downstream consumer of an unverified
   `VotePacket` performs redundant work (stake lookup, pool insertion,
   threshold evaluation) that a valid-but-forged packet should never trigger.

SIMD-0387 specifies how each validator registers its BLS12-381 public key in
its vote account. SIMD-0388 exposes the `sol_bls12_381_*` syscalls. This SIMD
specifies how those two primitives are composed at the consensus layer to
produce a complete, auditable signature-verification path for every inbound
`VotePacket`.

An Anza Research reviewer examining SIMD-0326 for promotion from `Draft` to
`Review` will identify the absence of `signature_set` verification as a
blocker: without it, the safety proof in the Alpenglow white paper (which
assumes that only stake-weighted validators can produce valid certificates) does
not hold at the implementation level. This SIMD resolves that blocker.


## New Terminology

**`VotePacket`** — the wire-format message sent between validators in the
Alpenglow Votor protocol, as defined in SIMD-0326. Contains a `vote_type`,
`slot`, `block_id`, and a `signature_set`.

**`SignatureSet`** — the field inside a `VotePacket` containing: (a) a
BLS12-381 G2 aggregate signature over the canonical vote message, and (b) a
compact bitfield identifying which validator indices (from the current epoch's
ordered validator set) contributed to the aggregate.

**`AggregatedPublicKey`** — the BLS12-381 G1 point obtained by summing the
individual G1 public keys of all validators indicated by the bitfield. Computed
on-the-fly from the epoch's validator-pubkey table (populated per SIMD-0387).

**`VoteMessage`** — the canonical 48-byte domain-separated byte string over
which every constituent validator signed. Defined as:

```
VOTE_DOMAIN_SEP  ||  le_u64(slot)  ||  block_id[0..32]
```

where `VOTE_DOMAIN_SEP = b"solana-alpenglow-vote-v1"` (24 bytes, zero-padded
to 32 bytes for alignment).

**`bls_vote_sigverify_enabled`** — the feature-gate pubkey that activates
mandatory `signature_set` verification. While this gate is inactive, inbound
`VotePacket`s are processed as they are today (no signature check). Once
activated, any packet that fails verification is dropped before pool insertion.


## Detailed Design

### Invariant

After this SIMD is activated, the following invariant **must** hold at every
votor pipeline entry-point:

> A `VotePacket` is admitted to the Pool if and only if
> `verify_vote_packet_signature(&packet, &epoch_bls_keys)` returns `Ok(())`.

Violations of this invariant at any processing node are a consensus safety bug
and must be treated with the same severity as a bank-hash mismatch.


### Algorithm

```rust
/// Entry point called once per inbound VotePacket, before pool insertion.
/// Returns Ok(()) if the aggregate BLS signature is valid.
/// Returns Err(SigVerifyError) and the packet MUST be silently dropped.
pub fn verify_vote_packet_signature(
    packet: &VotePacket,
    epoch_bls_keys: &EpochBlsKeyTable,
) -> Result<(), SigVerifyError> {
    // 1. Reject empty or oversized bitfields immediately.
    let n = epoch_bls_keys.len();
    if packet.signature_set.signer_bitfield.len_bits() != n {
        return Err(SigVerifyError::BitfieldLengthMismatch {
            expected: n,
            got: packet.signature_set.signer_bitfield.len_bits(),
        });
    }

    // 2. Require at least one signer.
    let signer_count = packet.signature_set.signer_bitfield.count_ones();
    if signer_count == 0 {
        return Err(SigVerifyError::EmptySignerSet);
    }

    // 3. Aggregate the public keys of all set bits.
    // This is O(k) scalar additions on G1 where k = signer_count.
    let mut agg_pubkey = G1Affine::identity();
    for idx in packet.signature_set.signer_bitfield.iter_ones() {
        let pk = epoch_bls_keys
            .get(idx)
            .ok_or(SigVerifyError::UnknownValidatorIndex(idx))?;
        agg_pubkey = (agg_pubkey + pk.0).into();
    }

    // 4. Reconstruct the canonical vote message.
    let msg = canonical_vote_message(
        packet.slot,
        &packet.block_id,
        packet.vote_type,
    );

    // 5. Verify the aggregate signature via SIMD-0388 syscall equivalent.
    // In the validator binary this calls the native blst or arkworks path;
    // the on-chain equivalent uses sol_bls12_381_g2_verify.
    bls12_381_verify_g2(
        &agg_pubkey,
        &packet.signature_set.aggregate_sig,
        &msg,
    )
    .map_err(|_| SigVerifyError::InvalidAggregateSignature)
}

/// Canonical 56-byte message bound to the vote type to prevent
/// cross-vote-type signature reuse.
fn canonical_vote_message(
    slot: Slot,
    block_id: &BlockId,
    vote_type: VoteType,
) -> [u8; 56] {
    let mut buf = [0u8; 56];
    // 24-byte domain separator (padded to 32)
    buf[0..24].copy_from_slice(b"solana-alpenglow-vote-v1");
    // vote_type discriminant in byte 31 prevents cross-type reuse
    buf[31] = vote_type as u8;
    // slot as little-endian u64
    buf[32..40].copy_from_slice(&slot.to_le_bytes());
    // first 16 bytes of block_id (full 32-byte version in extended form)
    buf[40..56].copy_from_slice(&block_id.0[0..16]);
    buf
}
```

**Note on `canonical_vote_message` length**: the full `block_id` (32 bytes)
should be included in production. The 16-byte truncation above is for
illustration only. Implementors MUST use all 32 bytes of `block_id`.


### Error Variants

All error variants cause the packet to be **silently dropped** (no gossip
propagation, no log at WARN or above in steady state, only a metrics counter
increment). Logging at WARN level is permissible during the first 100 epochs
after feature activation to assist operators in identifying misconfigured
validators.

| Variant | Meaning |
|---|---|
| `BitfieldLengthMismatch` | Bitfield does not match current epoch validator count |
| `EmptySignerSet` | No bits set; packet carries no stake weight |
| `UnknownValidatorIndex(idx)` | Bit set for an index with no registered BLS key per SIMD-0387 |
| `InvalidAggregateSignature` | Pairing check failed; signature is not valid |


### Feature-Gate Lifecycle

The feature gate `bls_vote_sigverify_enabled` follows the standard Solana
feature-gate activation process (SIMD-0089).

- **Before activation**: `verify_vote_packet_signature` is not called. All
  `VotePacket`s are admitted to the pool regardless of signature content. This
  is the current behaviour inherited from SIMD-0326.
- **After activation**: Every `VotePacket` must pass `verify_vote_packet_signature`
  before pool admission. Packets that fail are dropped and counted under the
  `vote_packet_sig_verify_failure` metric.
- **Rollback**: If a supermajority of validators deactivates the gate, the
  verification path is bypassed again. This rollback path exists only for
  emergency use and requires a coordinated upgrade.


### Compute Budget

BLS12-381 G1 point addition (step 3 above) and the final pairing (step 5)
are the dominant costs. Based on the benchmarks published in SIMD-0388:

| Operation | Approx. cost (validator CPU cycles) |
|---|---|
| G1 point addition per signer | ~4,200 cycles |
| BLS12-381 pairing (1 pair) | ~1,800,000 cycles |
| Full verify, k=2000 signers | ~10,200,000 cycles (~3.4 ms at 3 GHz) |
| Full verify, k=200 signers (typical) | ~2,220,000 cycles (~0.74 ms) |

Verification is performed off-chain in the validator binary, not via a
transaction or CPI, so it is not subject to the compute-unit budget. However,
because verification runs in the hot path of the Votor receive loop, validators
SHOULD pipeline verifications across CPU cores using a dedicated BLS thread
pool of size min(4, available_cores / 2) to avoid stalling the main Votor
state machine.

The runtime MUST NOT begin BLS verification for a batch of packets if fewer
than `SIGVERIFY_BATCH_MIN = 8` packets are ready; instead it MUST wait up to
`SIGVERIFY_BATCH_WAIT_MS = 2` milliseconds for the batch to fill. This amortises
the pairing overhead across multiple packets sharing the same aggregated key
when the cluster is operating near certificate thresholds.


### Interaction with Existing SIMDs

**SIMD-0326 (Alpenglow)**: This SIMD is a direct follow-on. SIMD-0326
introduced `VotePacket` and `SignatureSet` as data structures but explicitly
deferred verification. SIMD-0530 completes that deferral.

**SIMD-0387 (BLS pubkey management in vote account)**: The
`EpochBlsKeyTable` used in step 3 of the algorithm above is populated
from the BLS pubkeys registered per SIMD-0387. SIMD-0387 MUST be activated
before `bls_vote_sigverify_enabled` can be safely activated. Any validator
that has not registered a BLS pubkey per SIMD-0387 will produce votes whose
aggregate cannot be verified; those votes will be dropped after this SIMD
activates.

**SIMD-0388 (BLS12-381 syscalls)**: The `bls12_381_verify_g2` primitive in
step 5 of the algorithm maps directly to the `sol_bls12_381_g2_verify` syscall
introduced by SIMD-0388. The validator binary uses the native Rust equivalent
(via the `blst` crate) rather than the syscall itself, but the two must be
bitwise-equivalent to ensure that any future on-chain audit program can
re-verify historical aggregates.


## Alternatives Considered

### Defer to certificate construction only

Verification could be performed only when assembling a certificate (i.e., at
the 60%/80% stake threshold) rather than on every inbound `VotePacket`. This
reduces total CPU work because not every packet contributes to a certificate.
However, it allows unauthenticated votes to pollute the Pool, potentially
enabling a targeted memory exhaustion attack in which a Byzantine node sends
`MAX_POOL_VOTES` forged packets to fill the Pool before honest votes arrive.
Per-packet verification is therefore preferred.

### Batched Miller-loop verification

Rather than verifying each aggregate signature independently, multiple
`VotePacket`s from the same slot could be combined into a single multi-pairing
check using random linear combination (as used in Ethereum's consensus layer).
This reduces the per-packet pairing cost by roughly 40% at batch size 8. This
optimisation is NOT specified here to keep the initial implementation simple and
auditable. A future SIMD may add batched verification as a pure performance
optimisation with no consensus-level changes.

### Ed25519 fallback

Retaining Ed25519 per-validator signatures (as used in TowerBFT) and verifying
them individually was considered as a drop-in approach requiring no new
cryptography. This was rejected because: (a) it eliminates the bandwidth savings
that motivated BLS aggregation in SIMD-0326; (b) it requires O(k) ed25519
verifications per packet rather than O(k) G1 additions plus one pairing, which
is slower for large k; and (c) it diverges from the white paper's security
model.


## Impact

Validator operators will see a modest increase in CPU utilisation on the Votor
receive thread after feature activation, proportional to the number of inbound
`VotePacket`s per second. Based on current validator-set sizes (~1,700
validators) and Alpenglow's projected vote rate (~2,000 packets per slot at
400 ms slot time), the expected additional load is approximately 2–4 CPU cores
running in steady state on a typical validator machine (32+ core). Operators
running validators with fewer than 8 physical cores should increase their
hardware allocation before the feature activates.

Apps, wallets, and explorers are not affected. This change is entirely internal
to the validator's Votor pipeline.


## Security Considerations

This SIMD eliminates the ability to inject forged or replayed `VotePacket`s
into the Votor pipeline. The following attack classes are mitigated:

**Stake amplification**: A validator cannot claim to represent more stake than
it holds because the aggregated public key is derived from the on-chain BLS
key registrations (SIMD-0387), not from the packet itself.

**Cross-slot replay**: The `canonical_vote_message` binds the signature to
`(slot, block_id, vote_type)`. A valid signature for slot N cannot be replayed
for slot N+1 even if the same block_id is produced (which is impossible given
the PoH commitment but is nonetheless prevented at the signature layer).

**Cross-vote-type replay**: The `vote_type` discriminant in byte 31 of the
domain-separated message prevents a notarize signature from being replayed as
a finalize signature.

**Implementation note**: Implementors MUST use a constant-time BLS pairing
implementation. The `blst` crate (used by the Agave validator) provides
constant-time guarantees for the final exponentiation and Miller loop.


## Drawbacks

The primary drawback is the additional CPU cost on the Votor receive path.
For validators near the hardware minimum, this may require an upgrade before
`bls_vote_sigverify_enabled` activates.

A secondary drawback is the strict dependency ordering: SIMD-0387 must be
fully activated (all validators registered, epoch transition complete) before
this feature can safely activate. Tooling to detect validators without BLS
keys registered should be developed and deployed at least one epoch before
`bls_vote_sigverify_enabled` is scheduled for activation.


## Backwards Compatibility

This change is backwards-incompatible with any validator that has not
registered a BLS12-381 public key per SIMD-0387. After `bls_vote_sigverify_enabled`
activates, such a validator's votes will be cryptographically unverifiable and
will be silently dropped by all other validators, effectively excluding it from
reward eligibility. This is the correct and intended behaviour: it enforces
complete migration to the Alpenglow key infrastructure before the security
property is enforced.

Validators that were previously passing unverified `VotePacket`s will notice
no change in behaviour if they have correctly registered their BLS key and are
signing votes as specified in SIMD-0326.


## Bibliography

1. *Kniep, Sliwinski, Wattenhofer*, **Solana Alpenglow Consensus v1.1**, 2025,
   https://www.anza.xyz/alpenglow-1-1
2. SIMD-0326, *Alpenglow*,
   https://github.com/solana-foundation/solana-improvement-documents/blob/main/proposals/0326-alpenglow.md
3. SIMD-0387, *BLS Pubkey Management in Vote Account*,
   https://github.com/solana-foundation/solana-improvement-documents/blob/main/proposals/0387-bls-pubkey-management-in-vote-account.md
4. SIMD-0388, *BLS12-381 Syscalls*,
   https://github.com/solana-foundation/solana-improvement-documents/blob/main/proposals/0388-bls12-381-syscalls.md
5. *Boneh, Lynn, Shacham*, **Short Signatures from the Weil Pairing**, 2001,
   https://link.springer.com/article/10.1007/s00145-004-0314-9
6. `blst` library, https://github.com/supranational/blst
