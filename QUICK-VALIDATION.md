# Quick Validation — Try ABIS with your AI

**Repository:** [abis-standard/abis-reference-runtime](https://github.com/abis-standard/abis-reference-runtime)  
**Type:** Public validation entry — evidence gathering, **not** certification or conformance determination

---

## Hero

**Try ABIS with your AI**  
No coding required for Repository-Only Validation.

---

## 日本語

**ABISをAIで試してみる**

プログラミングやGitHubの専門知識は必要ありません。  
普段利用している生成AIの入力欄へ、下記スタータープロンプト（**生成AIへ入力するための文章**）をそのまま貼り付けて送信してください。AIがABIS Reference Runtimeをどこまで自力で理解・検証できるか確認できます。

---

## What this is

Quick Validation is the fastest public entry point into ABIS independent validation.

You do **not** need:

- programming
- a terminal
- `git clone`
- `curl`
- tokens or credentials

You **do** need:

- a generative AI assistant you already use (any provider)
- about 1–3 minutes to copy a **starter prompt** (ready-to-paste text for the AI input), paste it into the chat input, send it, and review the result

**Human step vs execution:** Pasting and sending the starter prompt is **not** the same as executing Tests, the Runtime, or HTTP requests.

Quick Validation uses **Repository-Only Validation** when live Runtime execution is not available. That mode is defined in [VALIDATION.md](VALIDATION.md). This page does not replace that guide — it helps you start.

Validation is evidence gathering. It is **not** ABIS certification, conformance determination, or Business Outcome evaluation.

---

## Validation scope

Report **one** scope for your session:

| Scope | Meaning |
| --- | --- |
| **REPOSITORY_ONLY** | You reviewed the public repository / docs / examples / source; you did **not** execute the Runtime in this session |
| **LIVE_RUNTIME** | You **actually executed** one or more Runtime operations and **directly observed** responses in this session |
| **INCOMPLETE** | Neither path completed — access, discovery, network, or environment limits. Still valid evidence |

`INCOMPLETE` is **not** worthless. See [VALIDATION.md — Validation scope](VALIDATION.md#validation-scope).

---

## Repository-only fallback

Runtime execution is **not** required for a useful validation report.

If your environment cannot execute the Runtime, continue as far as the public repository allows and mark execution-dependent steps as **NOT_EXECUTED**.

Do not infer live HTTP results from `examples/` or documented fixtures.

---

## Evidence honesty (brief)

When reviewing AI output, check that claims are labeled by source:

| Label | Meaning |
| --- | --- |
| Directly observed | From actual execution/retrieval in this session |
| Repository-described | From README, docs, source, fixtures, examples |
| Inferred | AI inference — not execution proof |
| Not executed | Operation was not performed |

Details: [VALIDATION.md — Evidence provenance](VALIDATION.md#evidence-provenance) · [evidence-report-template.md](validation/evidence-report-template.md)

---

## これは何か

Quick Validation は、ABIS の独立検証プログラムへの最短入口です。

**不要なもの**

- プログラミング
- ターミナル
- `git clone`
- `curl`
- トークンや認証情報

**必要なもの**

- 普段使っている生成AI（プロバイダは問いません）
- スタータープロンプト（生成AIへ入力するための文章）をコピーし、入力欄へ貼り付けて送信し、結果を確認する 1〜3 分程度

**人間の操作と実行の区別:** スタータープロンプトの貼り付け・送信は、Tests / Runtime / HTTP などの**実行**とは別の操作です。

Quick Validation では、Runtime を実行できない場合に **Repository-Only Validation** を利用します。このモードの定義は [VALIDATION.md](VALIDATION.md) にあります。本ページはそのガイドに取って代わるものではなく、開始を支援します。

検証はエビデンス収集です。**ABIS 認証・適合判定・Business Outcome 評価ではありません。**

---

## Beginner flow (3 steps)

```text
Open your generative AI assistant
  → Copy a starter prompt below (text to paste into the AI input)
  → Paste into the chat input and send
  → Review the AI's validation result
```

Sending the starter prompt is a human input step — not Runtime, HTTP, or test execution.

Optional next step: submit evidence through the existing GitHub Issue forms (links at the bottom).

---

## 初めての流れ（3ステップ）

```text
普段使う生成AIを開く
  → 下のスタータープロンプト（生成AIへ入力するための文章）をコピー
  → 生成AIの入力欄へそのまま貼り付けて送信
  → AI の検証結果を確認
```

スタータープロンプトの貼り付け・送信は人間の入力操作であり、Runtime / HTTP / Tests の実行ではありません。

任意の次のステップ: 既存の GitHub Issue フォームからエビデンスを提出（ページ末尾のリンク）。

---

## Step 1 — Open an AI assistant

Use any AI assistant you already have access to.

Examples include ChatGPT, Claude, Gemini, Grok, Copilot, or a custom agent — but **no specific provider is required or recommended**.

---

## ステップ 1 — AI アシスタントを開く

普段利用している AI アシスタントを使ってください。

ChatGPT、Claude、Gemini、Grok、Copilot、カスタムエージェントなどの例がありますが、**特定プロバイダの利用は必須でも推奨でもありません**。

---

## Step 2 — Copy and send a starter prompt

The blocks below are **starter prompts** — ready-to-paste text for your generative AI input. They are **not** commands to run locally.

Choose **English** or **Japanese**. Copy the block, paste it into your AI chat input, and send it.

Sending the starter prompt is a **human input step**. It is **not** the same as executing Tests, starting the Runtime, or sending HTTP requests.

These prompts intentionally **do not** give away the full validation procedure. The goal includes checking whether an AI can discover validation methods from the public repository alone.

---

## ステップ 2 — スタータープロンプトをコピーして送信

下記のブロックは **スタータープロンプト** — **生成AIへ入力するための文章**です。ローカルで実行するコマンドではありません。

**English** または **日本語** を選び、ブロックをコピーし、**生成AIの入力欄へそのまま貼り付けて送信**してください。

スタータープロンプトの貼り付け・送信は **人間の入力操作** です。Tests の実行、Runtime の起動、HTTP リクエストの送信とは**別の操作**です。

これらのプロンプトは、検証手順の正解を最初から教えません。公開 Repository だけから AI が検証方法を自力で発見できるかも確認目的の一部です。

---

### Starter prompt — English

```text
Please review the following public GitHub repository and validate the ABIS Reference Runtime using only publicly available information.

Distinguish information you directly observed, information described in the repository, inferred information, and operations you did not execute.

Do not report any operation as executed unless it was actually executed in your environment.

Report only what you could actually verify in this session.

If the repository contains validation instructions, follow them.

Repository:
https://github.com/abis-standard/abis-reference-runtime
```

---

### スタータープロンプト — 日本語

```text
以下の公開 GitHub Repository を確認し、公開情報だけを使って ABIS Reference Runtime を検証してください。

実際に確認した情報、Repository に記載されていた情報、推測した情報、実行していない操作を区別してください。

実際に実行できなかった操作は、実行したものとして報告しないでください。

このセッションで検証できた範囲だけを報告してください。

Repository 内に Validation 方法がある場合は、その指示に従ってください。

Repository:
https://github.com/abis-standard/abis-reference-runtime
```

---

## Step 3 — Review the result

Do **not** expect success only. Many outcomes are valid validation evidence.

| Outcome | Valid as evidence? |
| --- | --- |
| Could not access the repository | Yes |
| Could not discover a validation method | Yes |
| Stopped at repository understanding | Yes |
| Could not execute the Runtime | Yes |
| Completed Repository-Only Validation | Yes |
| Found ambiguity or a blocker | Yes |
| Completed live Runtime validation | Yes (if actually executed) |
| Session incomplete (access / discovery / environment) | Yes |

Classify your session scope: **REPOSITORY_ONLY**, **LIVE_RUNTIME**, or **INCOMPLETE**.

If the AI reports HTTP results, check whether they were **actually executed** or inferred from fixtures/examples. Files under `examples/` are documentation fixtures — **repository-described**, not proof of execution.

Do **not** treat validation success as conformance, certification, or "complete specification compliance".

---

## ステップ 3 — 結果を確認

成功だけを期待しないでください。多くの結果は有効な Validation Evidence です。

| 結果 | エビデンスとして有効？ |
| --- | --- |
| Repository にアクセスできなかった | はい |
| Validation 方法を発見できなかった | はい |
| Repository 理解で停止した | はい |
| Runtime を実行できなかった | はい |
| Repository-Only Validation まで完了した | はい |
| 曖昧さやブロッカーを発見した | はい |
| ライブ Runtime 検証を完了した | はい（実際に実行した場合） |
| セッション未完了（アクセス / 発見 / 環境制限） | はい |

セッション scope を分類してください: **REPOSITORY_ONLY** / **LIVE_RUNTIME** / **INCOMPLETE**

AI が HTTP 結果を報告した場合、**実際に実行した**のか、`examples/` などのフィクスチャから推測したのかを確認してください。`examples/` 配下は **Repository 記載情報**であり、実行の証拠ではありません。

検証結果を適合・認証・「仕様を完全に満たす」と結論づけないでください。

---

## Step 4 (optional) — Submit formal evidence

When you want to share results with the ABIS public validation program, use the **existing** GitHub Issue forms or the structured template.

| Channel | Link |
| --- | --- |
| **Validation Report** | [Open Validation Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) |
| **Problem / Ambiguity** | [Open Validation Problem Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-problem.yml) |
| **Evidence report template** | [validation/evidence-report-template.md](validation/evidence-report-template.md) |
| **Public pilot questionnaire** | [validation/public-pilot/questionnaire.md](validation/public-pilot/questionnaire.md) |

For the full validation guide (all modes, semantic boundaries, agent prompt): [VALIDATION.md](VALIDATION.md)

For developer execution (clone, localhost gateway, curl): [README.md — Quick Start](README.md#quick-start)

---

## ステップ 4（任意）— 正式なエビデンスを提出

ABIS 公開検証プログラムに結果を共有したい場合は、**既存の** GitHub Issue フォームまたは構造化テンプレートを使います。

| チャネル | リンク |
| --- | --- |
| **Validation Report** | [Validation Report Issue を開く](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) |
| **Problem / Ambiguity** | [Validation Problem Issue を開く](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-problem.yml) |
| **Evidence report template** | [validation/evidence-report-template.md](validation/evidence-report-template.md) |
| **Public pilot questionnaire** | [validation/public-pilot/questionnaire.md](validation/public-pilot/questionnaire.md) |

完全な検証ガイド（全モード・意味論的境界・エージェント用プロンプト）: [VALIDATION.md](VALIDATION.md)

開発者向け実行（clone・localhost ゲートウェイ・curl）: [README.md — Quick Start](README.md#quick-start)

---

## Boundaries (unchanged)

These public semantic boundaries apply to Quick Validation and all other validation paths:

| Concept | Rule |
| --- | --- |
| Interaction | ≠ Execution |
| Native Result | ≠ Business Outcome |
| Technical status | ≠ Business Outcome |
| Observe | ≠ Completion Determination |
| Validation | ≠ Certification · ≠ Conformance |

Reference Runtime Business Outcome scope: **`NOT_EVALUATED`**.

Details: [VALIDATION.md — Semantic boundaries](VALIDATION.md#semantic-boundaries-required)

---

## 境界（変更なし）

Quick Validation を含むすべての検証経路に、次の公開意味論的境界が適用されます。

| 概念 | ルール |
| --- | --- |
| Interaction | ≠ Execution |
| Native Result | ≠ Business Outcome |
| Technical status | ≠ Business Outcome |
| Observe | ≠ Completion Determination |
| Validation | ≠ Certification · ≠ Conformance |

Reference Runtime の Business Outcome スコープ: **`NOT_EVALUATED`**

詳細: [VALIDATION.md — Semantic boundaries](VALIDATION.md#semantic-boundaries-required)

---

## Learn · Try · Run

| Stage | What | Where |
| --- | --- | --- |
| **Learn ABIS** | Concept, architecture, specification | [abis-standard/abis](https://github.com/abis-standard/abis) |
| **Try ABIS** | Quick Validation — no coding required | This page |
| **Run ABIS** | Clone, run localhost gateway, developer validation | [README.md — Quick Start](README.md#quick-start) · [VALIDATION.md](VALIDATION.md) |

---

## Learn · Try · Run（導線）

| 段階 | 内容 | 場所 |
| --- | --- | --- |
| **Learn ABIS** | 概念・アーキテクチャ・仕様 | [abis-standard/abis](https://github.com/abis-standard/abis) |
| **Try ABIS** | Quick Validation — プログラミング不要 | 本ページ |
| **Run ABIS** | clone・localhost 実行・開発者向け検証 | [README.md — Quick Start](README.md#quick-start) · [VALIDATION.md](VALIDATION.md) |
