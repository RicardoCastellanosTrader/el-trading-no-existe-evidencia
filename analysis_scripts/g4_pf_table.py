# PARTE D — tabla PF G4 desde specialists best-source + PER_SYM staged (read-only).
import json

SYMS = ["LTCUSDT", "XLMUSDT", "ETCUSDT", "VETUSDT", "FETUSDT"]
report = json.load(open("deployment_package_grupo_4/deployment_report_grupo_4.json", encoding="utf-8"))
best = report["best_source_per_sym"]

print(f"{'SYM':<8} {'best_source':<16} {'cl':<3} {'name':<28} "
      f"{'pf_comb':>8} {'pf_fwd':>7} {'pf_fwd_floor':>12} {'tr_fwd':>7}")
print("-" * 100)

all_floor = []
notable = 0
ncells = 0
for sym in SYMS:
    # PF se reporta desde el specialist PER_SYM staged (artefacto físico en el package).
    d = json.load(open(f"regime_wf/{sym}_specialist_configs.json", encoding="utf-8"))
    for ck in sorted(d["clusters"], key=int):
        c = d["clusters"][ck]
        tc = c.get("top_configs", [])
        if not tc:
            continue
        t = tc[0]  # #1 specialist del cluster
        pf_comb = t.get("pf_combined", float("nan"))
        pf_fwd = t.get("pf_fwd", float("nan"))
        floor = t.get("pf_fwd_ci_low", float("nan"))
        trfwd = t.get("trades_fwd", 0)
        all_floor.append(floor)
        ncells += 1
        if pf_comb >= 1.5:
            notable += 1
        bs = best[sym] if ck == sorted(d["clusters"], key=int)[0] else ""
        print(f"{sym:<8} {bs:<16} {ck:<3} {c.get('name','')[:28]:<28} "
              f"{pf_comb:>8.2f} {pf_fwd:>7.2f} {floor:>12.2f} {trfwd:>7}")
    print()

import statistics
print("-" * 100)
print(f"Celdas (cluster×sym): {ncells} | notable pf_combined>=1.5: {notable}/{ncells} "
      f"({100*notable//ncells}%)")
print(f"pf_fwd_floor (ci_low): mean={statistics.mean(all_floor):.3f} "
      f"median={statistics.median(all_floor):.3f} min={min(all_floor):.3f} max={max(all_floor):.3f}")
print()
print("Composicion best-source (rho-selectivity):")
gs = report["grupo_summary"]
print(f"  PER_SYM={gs['n_per_sym_baseline_best']} ETH_SOURCE={gs['n_eth_source_best']} "
      f"BTC_SOURCE={gs['n_btc_source_best']} | "
      f"gate_a_pass={gs['n_gate_a_pass_total']} gate_b_violations={gs['n_gate_b_violations_total']}")
for sym in SYMS:
    m = report["metrics_table"][sym][best[sym]]
    print(f"  {sym}: {best[sym]:<16} rho_mean={m['rho_mean']:+.3f} rho_max={m['rho_max']:+.3f} "
          f"stable_pos={m['n_stable_positive']} strong_neg={m['n_strong_negative']} "
          f"gateB={'PASS' if m['gate_b_pass'] else 'FAIL'}")
