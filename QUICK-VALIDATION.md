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

専門知識やプログラミングは必要ありません。  
普段利用しているAIに公開Repositoryを渡し、AIがABIS Reference Runtimeをどこまで自力で理解・検証できるか確認できます。

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

- an AI assistant you already use (any provider)
- about 1–3 minutes to copy a starter prompt and review the result

Quick Validation uses **Repository-Only Validation** when live Runtime execution is not available. That mode is defined in [VALIDATION.md](VALIDATION.md). This page does not replace that guide — it helps you start.

Validation is evidence gathering. It is **not** ABIS certification, conformance determination, or Business Outcome evaluation.

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

- 普段使っている AI アシスタント（プロバイダは問いません）
- スタータープロンプトをコピーして結果を確認する 1〜3 分程度

Quick Validation では、Runtime を実行できない場合に **Repository-Only Validation** を利用します。このモードの定義は [VALIDATION.md](VALIDATION.md) にあります。本ページはそのガイドに取って代わるものではなく、開始を支援します。

検証はエビデンス収集です。**ABIS 認証・適合判定・Business Outcome 評価ではありません。**

---

## Beginner flow (3 steps)

```text
Open your AI assistant
  → Copy a starter prompt below
  → Review the AI's validation result
```

Optional next step: submit evidence through the existing GitHub Issue forms (links at the bottom).

---

## 初めての流れ（3ステップ）

```text
普段使う AI アシスタントを開く
  → 下のスタータープロンプトをコピー
  → AI の検証結果を確認
```

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

## Step 2 — Copy a starter prompt

Choose **English** or **Japanese**. Paste the prompt into your AI assistant.

These prompts intentionally **do not** give away the full validation procedure. The goal includes checking whether an AI can discover validation methods from the public repository alone.

---

## ステップ 2 — スタータープロンプトをコピー

**English** または **日本語** を選び、AI アシスタントに貼り付けてください。

これらのプロンプトは、検証手順の正解を最初から教えません。公開 Repository だけから AI が検証方法を自力で発見できるかも確認目的の一部です。

---

### Starter prompt — English

```text
Please review the following public GitHub repository and validate the ABIS Reference Runtime using only publicly available information.

Do not report any operation as executed unless it was actually executed in your environment.

If the repository contains validation instructions, follow them.

Repository:
https://github.com/abis-standard/abis-reference-runtime
```

---

### スタータープロンプト — 日本語

```text
以下の公開 GitHub Repository を確認し、公開情報だけを使って ABIS Reference Runtime を検証してください。

実際に実行できなかった操作は、実行したものとして報告しないでください。

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

If the AI reports HTTP results, check whether they were **actually executed** or inferred from fixtures/examples. Files under `examples/` are documentation fixtures — not proof of execution.

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

AI が HTTP 結果を報告した場合、**実際に実行した**のか、`examples/` などのフィクスチャから推測したのかを確認してください。`examples/` 配下のファイルはドキュメント用フィクスチャであり、実行の証拠ではありません。

---

## Step 4 (optional) — Submit formal evidence

When you want to share results with the ABIS public validation program, use the **existing** GitHub Issue forms. No changes to those forms are required for Quick Validation.

| Channel | Link |
| --- | --- |
| **Validation Report** | [Open Validation Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) |
| **Problem / Ambiguity** | [Open Validation Problem Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-problem.yml) |

For the full validation guide (all modes, semantic boundaries, agent prompt): [VALIDATION.md](VALIDATION.md)

For developer execution (clone, localhost gateway, curl): [README.md — Quick Start](README.md#quick-start)

---

## ステップ 4（任意）— 正式なエビデンスを提出

ABIS 公開検証プログラムに結果を共有したい場合は、**既存の** GitHub Issue フォームを使います。Quick Validation のためにフォーム変更は不要です。

| チャネル | リンク |
| --- | --- |
| **Validation Report** | [Validation Report Issue を開く](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) |
| **Problem / Ambiguity** | [Validation Problem Issue を開く](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-problem.yml) |

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
