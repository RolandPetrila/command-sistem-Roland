# Investigations

Bug analyses, root cause analysis (RCA), profiling, debug outputs cu valoare istorica.

## Cand muti aici

- Bug SEV1/SEV2 — RCA inainte de fix (`<data>_<bug-name>_rca.md`)
- Profiling result — bottleneck analysis pe modul/endpoint
- Debug session output — daca a dezvaluit invariant non-obvious
- Cross-module impact analysis — refactor mare

## Format recomandat

```
# RCA <Bug Title>
**Data:** YYYY-MM-DD
**Severitate:** SEV1/SEV2
**Modul afectat:** <name>

## Simptom
## Investigare (pasi)
## Cauza root
## Fix aplicat (commit ref)
## Preventie (regula adaugata daca relevant)
```

## Cand muti de aici

- Bug rezolvat + decizie generala → `.meta/decisions.yaml`
- Profiling rezolvat → `.archive/` cu link la commit
