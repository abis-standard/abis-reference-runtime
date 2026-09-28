# ABISを実装してみる / Build with ABIS

**ABIS Reference Runtime — Developer Preview v0.8.0**

まずは、1つの Interaction、1つの Mapping、1つの Native Result から始められます。

Start with one interaction, one mapping, and one Native Result.

これは認証制度、適合性判定、本番統合プログラム、パートナープログラム、推奨制度、Business Outcome が成立したことの証明ではありません。

This is **not** a certification program, conformance program, production integration program, partner program, endorsement program, or proof of Business Outcome.

---

## 小さく始める / Start small

すべてを実装する必要はありません。実験を始めるには、次の4つで十分です。

You do not need to implement everything. Enough to begin:

1. **One** published interaction — 公開されている Interaction を1つ選ぶ（例: `restaurant` / `reserve`）
2. **One** Sandbox, Mock, or in-process simulator — 対応する Sandbox / Mock / in-process simulator を1つ（選択した `execution_class` が対応する範囲のみ）
3. **One** field-level mapping — field-level mapping を1つ
4. **One** observed Native Result — Native Result を1つ観測する、または blocked / failed attempt を記録する

外部HTTP実行の対応範囲は Interaction ごとに異なります。すべての vertical で `AUTHORIZED_NON_PRODUCTION` や remote Sandbox HTTPS が使えるとは限りません。

External Runtime HTTP support is **interaction-specific**. Do not assume every vertical supports `AUTHORIZED_NON_PRODUCTION` or remote Sandbox HTTPS.

---

## 試し方を選ぶ / Choose your route

| やりたいこと / Goal | 入口 / Start here |
| --- | --- |
| コードを書かずに ABIS を理解する / Understand ABIS without code | [QUICK-VALIDATION.md](QUICK-VALIDATION.md) |
| Reference Runtime をローカルで動かす / Run locally | [README — Quick Start](README.md#quick-start) · [VALIDATION.md](VALIDATION.md) |
| 自分の Sandbox / Mock を接続する / Connect your Sandbox / Mock | [INTEGRATION.md](INTEGRATION.md) |
| 第三者管理の非本番 Sandbox で Controlled Interop を試す / Controlled third-party non-production Sandbox interop | [docs/interop/d11c/](docs/interop/d11c/)（ドキュメントパッケージ。ドキュメント単体で相互運用結果を意味しません / no interoperability result is implied by the docs alone） |
| ABIS semantics を独立して実装・ Mapping する / Independently implement or map ABIS semantics | 本ページ + 本リポジトリ外の normative public ABIS materials / this section + normative ABIS materials outside this repository |

### 独立実装 / Independent implementation (experimental)

自分の client、adapter、または semantic mapping を独立して実装できます。

You may build your own client, adapter, or semantic mapping experiment.

ただし、Independent Implementation は自動的に以下を意味しません：

An independent implementation is **not** automatically:

- ABIS conformant
- certified
- production ready
- validated by ABIS maintainers
- endorsed by ABIS or any provider

ChatGPT、Claude、Cursor、Codex などを利用した **AI-assisted development** も対象です。ただし、AI provider が ABIS または提出内容を推奨・承認していることを意味しません。

**AI-assisted development is allowed.** Assistant use does **not** imply provider endorsement of ABIS or your submission.

観察を共有する場合は適切な GitHub Issue テンプレートで sanitized developer evidence を提出してください。Issue を開いただけでは実行は独立検証されません。

Submit sanitized developer evidence through the appropriate GitHub Issue template when you want to share observations — participant reports are not independently verified execution merely because they are filed.

---

## 最小の実装実験 / Minimal experiment (supported paths only)

次の流れは、サポートされている経路のみを対象とします。Preflight ≠ remote reachability。Native Result ≠ Business Outcome。Invoke では `outcome_disposition` は該当する場合 **NOT_EVALUATED** が想定されます。

```text
Choose one published interaction
  → GET /v1/reference-profile and interaction Descriptor
  → document operation mapping (synthetic data)
  → POST Preflight (configuration/readiness — not remote reachability)
  → POST Invoke with an advertised execution_class only
  → capture native_result + execution_provenance + trace_reference
  → record outcome_disposition (expected NOT_EVALUATED on Invoke)
```

**Do not** invent undocumented APIs.  
**Do not** bypass Runtime security controls (arbitrary URLs, `REAL_EXTERNAL`, production targets, credential leakage).

未文書化 API の発明や、Runtime セキュリティ制御の迂回（任意 URL、`REAL_EXTERNAL`、本番ターゲット、認証情報の漏えい）は行わないでください。

### Execution classes（v0.8.0 概要 / summary）

| Class | 用途 / Typical use |
| --- | --- |
| `CONTROLLED_SIMULATOR` | 制御された in-process simulator — 既定。広告されている全 Interaction / default — in-process controlled simulators (all advertised interactions) |
| `AUTHORIZED_NON_PRODUCTION` | 明示的に許可された非本番 HTTP(S) 境界 — **restaurant / `reserve` のみ**、ローカル設定時（localhost Mock または remote authorized Sandbox HTTPS） / authorized HTTP(S) boundary — **restaurant / `reserve` only** when locally configured |
| `REAL_EXTERNAL` | **DENY** |

`shopping` / `submit_order`: **`CONTROLLED_SIMULATOR` only** — 外部 Sandbox 実行は **NOT_IMPLEMENTED** / external Sandbox execution is **NOT_IMPLEMENTED**.

---

## どんな結果でも Evidence になる / Useful evidence (what to record)

成功した実行だけが Evidence ではありません。以下も有用な developer evidence です：

Helpful developer evidence may include:

- successful execution
- failed execution
- blocked execution（policy、validation、egress）
- mapping ambiguity
- documentation ambiguity
- environment limitation

### Evidence authority

| Source | Label |
| --- | --- |
| あなたが実行した Runtime HTTP レスポンス / Your live Runtime HTTP responses | **ACTUALLY_EXECUTED**（実行した場合 / when you ran them） |
| 本リポジトリの `examples/` / Files under `examples/` in this repo | **REPOSITORY_DESCRIBED** — 観測された実行ではない / not observed execution |
| 提出したレポート / Your written report | **PARTICIPANT_REPORTED** 等の developer evidence — 自動的な certification ではない / not automatic certification |

自分で実行したという記録（**ACTUALLY_EXECUTED**）と、第三者が再現・確認したこと（**REPRODUCED_BY_REVIEWER**）は同じではありません。

Distinguish **what you ran** from **what the repository describes**. **ACTUALLY_EXECUTED** ≠ **REPRODUCED_BY_REVIEWER**.

---

## 意味を混同しない / Semantic firewall

| Statement | 意味 / Meaning |
| --- | --- |
| **Interaction ≠ Execution** | Interaction を選んだだけでは、すべての execution class や外部経路が使えるとは限らない |
| **Native Result ≠ Business Outcome** | 外部サービスが `CONFIRMED` や `SUCCESS` を返しても、利用者が意図した成果が成立した証明にはならない / `external_status` such as `CONFIRMED` is not Business Outcome success |
| **Technical Status ≠ Business Outcome** | トランスポート上の受理は outcome 評価ではない |
| **Observe ≠ Completion Determination** | Restaurant `observe` は technical/native のみ。外部 adapter Invoke では未サポート |
| **Validation ≠ Certification** | 本 Reference Runtime の validation は ABIS certification ではない |
| **Validation ≠ Conformance** | ここでのテスト合格は normative ABIS conformance を意味しない |
| **Independent implementation ≠ Conformance** | 独自実装は実験であり certified ではない |
| **NOT_IMPLEMENTED** | 能力境界（例: shopping の外部 HTTP） |
| **NOT_EVALUATED** | 本 Runtime スコープでの Invoke `outcome_disposition`（Business Outcome） |

**Business Outcome** in Reference Runtime scope: **`NOT_EVALUATED`**（ABIS が自動的に Business Outcome を判定するわけではありません / ABIS does not automatically determine Business Outcome here).

---

## 安全境界 / Safety boundaries (unchanged)

- **REAL_EXECUTION PROHIBITED** · **REAL_EXTERNAL DENY**
- 本番実行なし · 実予約なし · 実購入なし · 実決済なし / No production execution · no real booking · no real purchase · no real payment
- Remote Sandbox は **明示的に許可・設定された場合のみ**（`REMOTE_AUTHORIZED`、trusted config） / Remote Sandbox only where **explicitly authorized and configured**
- 任意 URL プロキシなし / No arbitrary URL proxy

---

## Evidence を提出する / Report and integrate

| 目的 / Intent | Link |
| --- | --- |
| Validation evidence | [Validation Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) |
| Integration evidence（Sandbox/Mock + Reference Runtime） | [Integration Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=integration-report.yml) |
| Independent implementation / builder evidence | [Independent Builder Report](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=independent-builder-report.yml) |

実装が成功しなかった場合でも提出できます。blocked / failed / ambiguous results も valid evidence です。

Independent Builder は別の **progression** と **evidence-authority** モデルを使います — [docs/independent-builders/](docs/independent-builders/README.md)。実験的な developer evidence であり、certification や conformance ではありません。

See also [INTEGRATION.md](INTEGRATION.md) for execution-class detail and [CHANGELOG.md](CHANGELOG.md) for version history.
