# DEPLOYMENT RUNBOOK — Grupo N Bot v2.X.Y → v2.X+1.0

**Canonical procedure cumulative cross-Sub-Sesiones precedent absoluto**
**Established**: 2026-05-17 post-Grupo-1 deployment cumulative
**Target ETA Ricardo intervention**: ~10-20 min total cumulative (vs ~3h Sub-Sesión 2026-05-11/17 cumulative)

---

## 0. Goal cumulative

Future deployments Grupos 2-9 cumulative must NOT repeat the operational obstacles encountered en Sub-Sesión 2026-05-11/17 cumulative:
- Empty SSH credentials environment cumulative
- IAM Claude-Helper read-only cumulative
- SSM Agent not installed VPS cumulative
- EC2 Instance Connect AWS SG restrictions cumulative
- sudo password requirement cumulative
- Multiple iterations Ricardo step-by-step cumulative

**Now ALL these prerequisites are RESOLVED cumulative permanente** (see §1 below).

---

## 1. VPS deployment infrastructure ESTABLISHED cumulative

### 1.1 AWS instance cumulative

| Field | Value |
|---|---|
| Instance ID | `INSTANCE_ID_TOKIO_REDACTADO` |
| Region | `ap-northeast-1` (Tokyo) |
| AZ | `ap-northeast-1a` |
| Public IP | `IP_VPS_TOKIO_REDACTADA` |
| Type | t3.micro |
| Security Group | `sg-008d8be6985339a90` (trading-bot-sg) |
| IAM Role attached | `EC2-SSM-Role` (AmazonSSMManagedInstanceCore policy) |
| SSM Agent installed | ❌ **NOT installed** — DEFERRED future Sub-Sesión dedicated |
| OS | Ubuntu 22.04+ (usrmerge `/bin -> /usr/bin`) |

### 1.2 VPS bot setup cumulative

| Field | Value |
|---|---|
| Linux user | `trader` |
| Bot service | `/etc/systemd/system/trading-bot.service` (SYSTEM systemd) |
| Bot path | `/home/trader/combolab/` |
| Specialists path | `/home/trader/combolab/regime_wf/` |
| Logs path | `/home/trader/combolab/logs/engine.log` |
| Python venv | `/home/trader/venv/bin/python` |
| Command | `python -m live.live_engine --live --confirm-live` |

### 1.3 Local PC Ricardo cumulative

| Field | Value |
|---|---|
| SSH key (private) | `~/.ssh/trading_vps` (ed25519) |
| SSH key (public) | `~/.ssh/trading_vps.pub` |
| AWS CLI | `python -m awscli` (boto3 NOT installed; awscli Python pkg 1.44.75 cumulative) |
| AWS credentials | `~/.aws/credentials` [default] (IAM Claude-Helper) |
| AWS region default | `ap-northeast-1` |

### 1.4 IAM Claude-Helper cumulative permissions PERMANENT cumulative

| Resource | Permission |
|---|---|
| Account | AWS_ACCOUNT_REDACTADO |
| IAM user | `Claude-Helper` |
| ARN | `arn:aws:iam::AWS_ACCOUNT_REDACTADO:user/Claude-Helper` |
| Baseline permissions cumulative | `sts:GetCallerIdentity` + `ec2:DescribeInstances` |
| **Inline policy** `ClaudeHelperGrupo1DeploymentInline` cumulative (ATTACHED 2026-05-17): | |
| - `ssm:DescribeInstanceInformation` | `*` |
| - `ssm:SendCommand` | `INSTANCE_ID_TOKIO_REDACTADO` + AWS-RunShellScript |
| - `ssm:GetCommandInvocation` + related | `*` |
| - `ec2-instance-connect:SendSSHPublicKey` | `INSTANCE_ID_TOKIO_REDACTADO` |
| - `s3:*` (CRUD) | `claude-helper-deployment-staging` bucket |

### 1.5 VPS sudoers PERMANENT cumulative

**File**: `/etc/sudoers.d/trader-trading-bot` (0440 root:root)
**Installed**: 2026-05-17
**Purpose**: Least-privilege NOPASSWD sudo para `trader` user — solo trading-bot.service operations

```
# Allow trader to manage trading-bot.service operations cumulative
trader ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop trading-bot.service
trader ALL=(ALL) NOPASSWD: /usr/bin/systemctl start trading-bot.service
trader ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart trading-bot.service
trader ALL=(ALL) NOPASSWD: /usr/bin/systemctl status trading-bot.service
trader ALL=(ALL) NOPASSWD: /usr/bin/systemctl status trading-bot.service --no-pager
trader ALL=(ALL) NOPASSWD: /usr/bin/systemctl is-active trading-bot.service
trader ALL=(ALL) NOPASSWD: /usr/bin/systemctl show trading-bot.service -p ActiveEnterTimestamp
trader ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u trading-bot.service -n [0-9]*
trader ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u trading-bot.service -n [0-9]* --no-pager
trader ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u trading-bot.service --since *
trader ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u trading-bot.service --since * -n [0-9]* --no-pager
trader ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u trading-bot.service --since * -p err --no-pager
trader ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u trading-bot.service --since * -p warning --no-pager
trader ALL=(ALL) NOPASSWD: /usr/bin/chown trader\:trader /home/trader/combolab/regime_wf/*
trader ALL=(ALL) NOPASSWD: /bin/systemctl stop trading-bot.service
trader ALL=(ALL) NOPASSWD: /bin/systemctl start trading-bot.service
trader ALL=(ALL) NOPASSWD: /bin/systemctl status trading-bot.service
trader ALL=(ALL) NOPASSWD: /bin/systemctl is-active trading-bot.service
```

### 1.6 Security Group whitelist cumulative

- Ricardo IP whitelisted en `sg-008d8be6985339a90` port 22 SSH cumulative (description `Ricardo-deploy-grupo-1-2026-05-17`).
- **Verify IF Ricardo IP changes cumulative** (e.g., new ISP/VPN cumulative) — update SG whitelist primero cumulative.

---

## 2. Canonical deployment procedure cumulative Grupo N (target ~10-20 min)

### Step 1 — Pre-flight verification cumulative (~2 min)

Ricardo local PC cumulative:

```bash
cd /c/Users/rixip/combolab

# 2.1 Verify deployment package ready cumulative
ls -la deployment_package_grupo_N/*.json
md5sum deployment_package_grupo_N/*.json
cat deployment_package_grupo_N/deployment_report_grupo_N.json | python -m json.tool | head -50

# 2.2 Verify Ricardo current IP matches SG whitelist cumulative
echo "My IP: $(curl -s ifconfig.me)"
# IF IP changed since 2026-05-17 cumulative → update sg-008d8be6985339a90 inbound rule cumulative

# 2.3 SSH connectivity test cumulative
ssh -i ~/.ssh/trading_vps -o ConnectTimeout=5 trader@IP_VPS_TOKIO_REDACTADA 'echo SSH_OK; uptime'

# 2.4 Sudo NOPASSWD verification cumulative
ssh -i ~/.ssh/trading_vps trader@IP_VPS_TOKIO_REDACTADA 'sudo -n systemctl is-active trading-bot.service'
```

### Step 2 — Ricardo authorization Tier 3 explicit cumulative (~1 min)

Ricardo prompt template para Claude Code cumulative:

```
ULTRATHINK máximo cumulative cross-Sub-Sesiones precedent absoluto.

DELEGACIÓN TOTAL AUTORIZADA Grupo N deployment cumulative — Claude Code ejecuta autonomous via Bash tool cumulative.

Composition Deploy <X>:
- [list 5 sym ← source per analysis cumulative]

Authorization explicit cumulative:
- AUTHORIZE Claude Code autonomous execution end-to-end vía SSH cumulative.
- AUTHORIZE auto-confirm per-step pauses internal cumulative.
- ÚNICOS Tier 3 PAUSE triggers Ricardo cumulative:
  - T3.1 open positions exposure > 50 USDT cumulative.
  - T3.2 deployment falla irrecuperable + rollback también falla cumulative.
  - T3.3 bot fails to start POST rollback retry cumulative.
- Reporte único cumulative al completion cumulative.

Procede deployment end-to-end cumulative.
```

### Step 3 — Claude Code autonomous deployment cumulative (~5-10 min)

Claude Code via Bash tool ejecuta cumulative:

```bash
TS=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/c/Users/rixip/combolab/deploy_grupo_N_${TS}.log"
BACKUP_DIR="/home/trader/combolab/regime_wf.bak-grupo_N-${TS}"
LOCAL_PKG="/c/Users/rixip/combolab/deployment_package_grupo_N"
SYMS=(SYM1USDT SYM2USDT SYM3USDT SYM4USDT SYM5USDT)  # adjust per grupo cumulative

# === State snapshot cumulative ===
ssh -i ~/.ssh/trading_vps trader@IP_VPS_TOKIO_REDACTADA 'bash -s' <<'EOF' | tee -a "$LOG_FILE"
sudo systemctl status trading-bot.service --no-pager | head -8
md5sum /home/trader/combolab/regime_wf/SYM{1,2,3,4,5}USDT_specialist_configs.json
tail -200 /home/trader/combolab/logs/engine.log | grep -E "posiciones abiertas|Balance USDT" | tail -3
EOF

# === Tier 3 trigger T3.1 check: exposure > 50 USDT? ===
# Manual evaluation OR scripted check on margin used vs threshold

# === STOP bot ===
STOP_TS=$(date +%s)
ssh -i ~/.ssh/trading_vps trader@IP_VPS_TOKIO_REDACTADA 'sudo systemctl stop trading-bot.service && sleep 2 && sudo systemctl is-active trading-bot.service || echo inactive'

# === Backup ===
ssh -i ~/.ssh/trading_vps trader@IP_VPS_TOKIO_REDACTADA "mkdir -p '$BACKUP_DIR' && cp /home/trader/combolab/regime_wf/SYM{1,2,3,4,5}USDT_specialist_configs.json '$BACKUP_DIR'/"

# === Upload + md5 verify ===
for sym in "${SYMS[@]}"; do
    LOCAL_MD5=$(md5sum "$LOCAL_PKG/${sym}_specialist_configs.json" | awk '{print $1}')
    scp -i ~/.ssh/trading_vps -q "$LOCAL_PKG/${sym}_specialist_configs.json" "trader@IP_VPS_TOKIO_REDACTADA:/home/trader/combolab/regime_wf/${sym}_specialist_configs.json.new"
    REMOTE_MD5=$(ssh -i ~/.ssh/trading_vps trader@IP_VPS_TOKIO_REDACTADA "md5sum /home/trader/combolab/regime_wf/${sym}_specialist_configs.json.new | awk '{print \$1}'")
    [[ "$LOCAL_MD5" == "$REMOTE_MD5" ]] || { echo "MD5 mismatch $sym"; exit 1; }
    ssh -i ~/.ssh/trading_vps trader@IP_VPS_TOKIO_REDACTADA "mv /home/trader/combolab/regime_wf/${sym}_specialist_configs.json.new /home/trader/combolab/regime_wf/${sym}_specialist_configs.json && sudo chown trader:trader /home/trader/combolab/regime_wf/${sym}_specialist_configs.json"
done

# === START bot ===
ssh -i ~/.ssh/trading_vps trader@IP_VPS_TOKIO_REDACTADA 'sudo systemctl start trading-bot.service'
sleep 30

# === Verify ===
ssh -i ~/.ssh/trading_vps trader@IP_VPS_TOKIO_REDACTADA 'sudo systemctl is-active trading-bot.service; sudo systemctl status trading-bot.service --no-pager | head -8; tail -30 /home/trader/combolab/logs/engine.log'

# === Error count post-start ===
ssh -i ~/.ssh/trading_vps trader@IP_VPS_TOKIO_REDACTADA 'tail -100 /home/trader/combolab/logs/engine.log | grep -ciE "error|critical|fatal|traceback" | grep -v "0 errores"'

echo "DOWNTIME=$(($(date +%s) - STOP_TS))s"
echo "BACKUP_DIR=$BACKUP_DIR"
```

Expected downtime cumulative: ~100-150s (analog Grupo 1 cumulative 127s).

### Step 4 — Update orchestrator state cumulative (~30s)

```bash
python -c "
import automation_orchestrator as ao
o = ao.AutomationOrchestrator()
o.load_state()
o.authorize_deploy(N)
o.transition(ao.STATE_DEPLOYED, note='autonomous_deploy_grupo_N_<TS>')
o.mark_deployment_ack(N)
o.transition(ao.STATE_NEXT_GRUPO, note='grupo_N_deployed_ok')
"
```

### Step 5 — Update memoria persistente cumulative (~2 min)

Crear `project_grupo_N_deployed_v2_X_0_<TS>.md` cumulative siguiendo template Grupo 1 + actualizar `MEMORY.md` index cumulative.

### Step 6 — Reporte único cumulative Ricardo deployment complete cumulative

Single comprehensive Tier 2 status report cumulative + invariantes preserved cross-Sub-Sesiones precedent absoluto.

---

## 3. Tier 3 PAUSE triggers cumulative MANDATORY

| Trigger | Condition | Action |
|---|---|---|
| **T3.1** | Open positions exposure > 50 USDT cumulative | PAUSE + Ricardo decision force-flat o defer |
| **T3.2** | Deployment falla irrecuperable + rollback también falla cumulative | PAUSE + Ricardo manual VPS investigation |
| **T3.3** | Bot fails to start POST rollback retry cumulative | PAUSE + Ricardo SSH manual fix |
| **T3.4** | MD5 mismatch upload (3 retries fail) | PAUSE + Ricardo investigate network/disk |
| **T3.5** | Errors detected en first 5 min post-start (>3 ERROR/CRITICAL log entries) | PAUSE + rollback + investigate |

---

## 4. Rollback procedure cumulative

```bash
bash /c/Users/rixip/combolab/deploy/rollback_grupo_1.sh /home/trader/combolab/regime_wf.bak-grupo_N-<TS>/
```

The rollback script (existing cumulative `deploy/rollback_grupo_1.sh` cumulative) is generic — works para cualquier Grupo cumulative con backup_dir path provided cumulative.

Rollback effect cumulative:
1. Stop bot v2.X+1.0 (failed deploy)
2. Preserve failed specialists at `regime_wf.failed-deploy-<TS>/` cumulative
3. Restore 5 specialists from backup cumulative
4. Start bot v2.X.Y baseline (previous version cumulative)

---

## 5. Lecciones aprendidas Sub-Sesión 2026-05-11/17 cumulative cross-Sub-Sesiones precedent absoluto

### 5.1 Empirical takeaways cumulative

1. **AWS CLI available via `python -m awscli`** cumulative — NOT direct `aws` executable. `boto3` NOT installed cumulative.
2. **EC2 Instance Connect** cumulative funciona para `ubuntu` user con 60s key window cumulative.
3. **Ubuntu user tiene sudo NOPASSWD inherent** cumulative (cloud-init default).
4. **sudoers path matters cumulative**: `/usr/bin/systemctl` (Ubuntu 22.04+) ≠ `/bin/systemctl` aunque symlink — include AMBOS paths cumulative en sudoers.
5. **sudoers args matter cumulative**: `--no-pager` etc. requieren explicit rules OR `*` wildcard cumulative.
6. **SSH heredoc + sudo cumulative**: sin TTY allocated cumulative, `sudo` (no -n) falla "terminal required" si NOPASSWD no aplica cumulative — use `sudo -n` o ensure NOPASSWD rules match exact command cumulative.
7. **Stash apply preserva working tree** v18 R1 chunked cumulative durante deployment cumulative.
8. **Bot v2.4.5 ~25 días uptime continuous cumulative** demostró stability cumulative pre-deploy cumulative.
9. **Pre-existing divergence Brain ↔ Kernel ETH+TRX cumulative** = NOT v18-induced (Option α investigation cumulative).

### 5.2 Operational improvements cumulative para Grupos 2-9

1. **Ricardo authorization template cumulative** (§2 Step 2) — copy-paste cumulative para minimize iteration.
2. **Claude Code autonomous via Bash tool cumulative** — NOT script execution Ricardo manual cumulative.
3. **Auto-confirm per-step pauses internal cumulative** bajo Ricardo prior authorization cumulative.
4. **Tier 3 PAUSE ONLY genuinely critical cumulative** (T3.1-T3.5 cumulative).
5. **Skip iterative SSH discovery cumulative** — infrastructure ESTABLISHED §1 cumulative.

---

## 6. Pre-flight checklist cumulative para Grupos 2-9

Antes de iniciar deployment Grupo N cumulative, verify:

- [ ] `deployment_package_grupo_N/` cumulative ready (5 JSONs + report.json) — output Fase D.6 ANALYSIS step cumulative
- [ ] `automation_state.json` cumulative en `DEPLOYMENT_READY_GRUPO_N` con `tier3_gate_pending=true` cumulative
- [ ] Ricardo IP whitelisted SG sg-008d8be6985339a90 (verify cumulative `curl ifconfig.me` matches SG cumulative)
- [ ] SSH connectivity test cumulative PASS
- [ ] Sudo NOPASSWD test cumulative PASS (`ssh ... sudo -n systemctl is-active trading-bot.service`)
- [ ] Ricardo authorization Tier 3 explicit cumulative (§2 Step 2 template)

POST checklist PASS cumulative → Claude Code procede autonomous deployment cumulative ~10-20 min total cumulative.

---

## 7. Cleanup post-deployment optional cumulative

Si Ricardo desea restaurar security boundaries cumulative post-24-48h satisfactory cumulative:

```bash
# Remove inline IAM policy (vuelve READ-ONLY EC2 describe baseline)
python -m awscli iam delete-user-policy --user-name Claude-Helper --policy-name ClaudeHelperGrupo1DeploymentInline

# Remove sudoers cumulative (vuelve sudo password requirement)
ssh -i ~/.ssh/trading_vps trader@IP_VPS_TOKIO_REDACTADA 'sudo rm /etc/sudoers.d/trader-trading-bot'
```

**Caveat cumulative**: Removing these cumulative bloqueará future Grupos 2-9 autonomous deployments cumulative — Ricardo decides tradeoff cumulative.

**Recomendación cumulative**: MANTENER cumulative durante deployment cycle Grupos 1-9 cumulative + cleanup POST Grupo 9 deployment cumulative cross-Sub-Sesiones precedent future cumulative.

---

## 8. Lección cardinal deploys de CÓDIGO — dependency-closure (2026-06-12)

**Origen empírico**: intento de reconciliación brain+portfolio VPS↔HEAD 2026-06-12 falló con
`ImportError: No module named 'mean_reversion_features'` en el restart (módulo nuevo de A05
nunca propagado al VPS). Rollback limpio, sin pérdida. **Era prevenible.**

**Regla MANDATORY cumulative**:
- **Deploys de CÓDIGO** (`live/*.py`, kernel, módulos de proyecto): ANTES del restart, verificar
  el **dependency-closure COMPLETO en el destino** — todo módulo que el código nuevo importe
  (directa y transitivamente) debe existir en el VPS a una versión compatible. Método: en el VPS,
  `python -c "import live.live_engine"` (o el entrypoint) en el venv **antes** de `systemctl start`.
  Si el import falla → abortar + rollback ANTES de tocar el servicio. Construir el manifest del
  deploy desde el closure real, no desde la lista de archivos "que parecen haber cambiado".
- **Deploys de DATOS** (`regime_wf/*_specialist_configs.json`, `regime_models/*_regime.joblib`):
  EXENTOS del closure-check — son datos que el bot carga al arranque, sin nuevas dependencias de import.
  PERO sujetos al **PROVENANCE GATE** (abajo).

**PROVENANCE GATE — MANDATORY en TODO deploy de DATOS (2026-06-12, post-auditoría forense)**:
- **Origen empírico**: misassignment GMM↔specialist en 11/20 símbolos (3 variantes: G1 GMMs stale
  de abril nunca actualizados en v2.5.0; cross-source sin GMM del source empaquetado; ADA joblib
  regenerado 18 min después de su JSON). Sobrevivió 4 deploys + certificación Capa 1+2 porque
  ningún paso verificaba que el specialist viajara con su GMM COMPAÑERO DE GENERACIÓN.
  Evidencia completa: `audit_forense_gap_20260612/INFORME_AUDITORIA_FORENSE_GAP.md`.
- **Regla**: ANTES de todo deploy de specialists/GMM, ejecutar
  `python deploy/provenance_gate.py --package <dir> --report <deployment_report_grupo_N.json>`
  → exit 0 obligatorio. Checks: P1 nombres de cluster JSON==joblib (permutación), P2a cutoff de
  training ≤ generated (companion regenerado), P2b gap cutoff→generated ≤7d (era stale),
  C1 md5 joblib target == joblib del SOURCE (cross-source), C2 formato cross-class del JSON.
- Los specialists y sus GMM **viajan JUNTOS en el mismo deploy** (lección G3 + hoy: en G1 el GMM
  no viajó y nadie lo notó durante 26 días).
- Validación bidireccional del gate 2026-06-12: contra el estado pre-fix detecta exactamente los
  11 símbolos del audit (P1×4 + P2b×4 + C1×6); contra el estado post-fix 19/19 PASS.
- Recomendado: barrido completo del estado VPS (JSONs+joblibs descargados o snapshot) en cada
  deploy, no solo del package incremental.

**Corolario de fidelidad §0.3**: un deploy de código que cruza muchas semanas de evolución
(p.ej. swap del stack de señales abril→junio) NO se valida solo con el gate de auto-consistencia
local (HEAD-brain↔HEAD-kernel). Requiere **shadow-equivalence sobre datos live** (señales del
stack viejo vs nuevo sobre las mismas velas, ≥98% entry-match, discrepancias explicadas) — ver
§13.3 "upgrade stack de señales live".

---

**ULTRATHINK máximo robust empirical-evidence-driven cumulative cross-Sub-Sesiones precedent absoluto**.
