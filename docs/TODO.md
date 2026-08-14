# やること・相談メモ

このファイルは「次に着手する候補」を溜めておく場所です。着手して完了したものは
`docs/CHANGELOG.md` へ移し、ここからは消します。

---

## 1. `docs/keymap-phase1.md` のファイル名を再考する

**依頼日**: 2026-08-12

当初は「Phase 1 の設計メモ」として作られたが、実際にはレイヤー設計・実装経緯・
LED配色・依存モジュール構成・今後の拡張案まで載る**総合ドキュメント**になっており、
ファイル名と中身が乖離している。

### 調査結果と提案（2026-08-12）

**実態**: 375行・15節。中身は「Phase 1 の設計メモ」ではなく、目的/前提/設計方針 →
レイヤー詳細リファレンス → 実装の仕組み（LED配色・AML・慣性スクロール・ジェスチャー）
→ 依存モジュール → ビルド手順 → 今後の構想、という**総合ドキュメント**。

決定的なのは、**ファイル冒頭の H1 が既に
`# moNa2 キーマップ — 設計・実装ドキュメント` になっている**こと。
中身も見出しも「phase1」を名乗っていないのはファイル名だけで、乖離は明白。

**提案する名前**: **`docs/design.md`**

理由は、既にある `docs/CHANGELOG.md`（履歴）/ `docs/TODO.md`（これから）と並べたとき、
`design.md`（今どうなっているか）で3点が綺麗に揃うから。用途で分かれていて短い。

代案: `docs/keymap.md`（対象がキーマップだと明示できる）/
`docs/keymap-design.md`（最も説明的だが冗長）

**併せてやるべき構造の整理**:

`keymap-phase1.md` の「Phase 2（今後の検討）」節（大西配列・薙刀式の案A〜D、
その他の検討事項）は、この `TODO.md` と役割が重複している。**Phase 2 節は
TODO.md へ移し**、設計ドキュメント側は「現状の説明」に徹させたい。
そうすれば「将来の話をどっちに書くか」の迷いが無くなる。

**改名時に追従が必要な参照**:

| ファイル | 箇所 | 対応 |
|---|---|---|
| `README.md` | 2箇所（187行・204行） | 書き換える |
| `docs/TODO.md` | 2箇所 | 書き換える |
| `old/README2.md` | 1箇所 | 廃止済みファイルなので放置でよい |
| `docs/CHANGELOG.md` | 6箇所 | **書き換えない**。過去の変更記録は当時の事実なので、改名した事実を新エントリに書くほうが正しい |

---

## 2. 薙刀式の実装 — ZMK v0.4 移行で状況が変わったか調査する

**依頼日**: 2026-08-12 / **優先度**: 本人の希望は高い（「やっぱり使いたい」）

`docs/keymap-phase1.md` の Phase 2「大西配列・薙刀式 導入案」で案A〜Dを検討し、
案C（`zmk-naginata` モジュール方式）は **DYAフォーク `v0.3-branch+dya` との互換性が
未確認**という理由で保留していた。

### 調査結果（2026-08-12 時点）— 見通しは大きく好転した

本家モジュールは **[`eswai/zmk-naginata`](https://github.com/eswai/zmk-naginata)**
（`main` = `316bcb5b76b5`、最終更新 2026-07-05）。以前検討したときの懸念は
ほぼ解消している。

| 確認項目 | 結果 |
|---|---|
| 想定する ZMK | `zmkfirmware/zmk` の **`main`**（= v0.4 系）。旧 v0.3 前提ではない |
| 保守状況 | 2026-07-05 更新。濁音連続の不具合修正や Windows 対応が入っており活発 |
| 使用している ZMK API | `drivers/behavior.h` / `zmk/behavior.h` / `zmk/behavior_queue.h` / `zmk/event_manager.h` / `zmk/events/keycode_state_changed.h` |
| **`main+dya`（我々の pin）側での API 存在確認** | **5ヘッダすべて存在**。`raise_zmk_keycode_state_changed_from_encoded()` も `behavior_driver_api.binding_pressed/released` もシグネチャ一致 |

つまり **v0.3 時代に保留した理由（DYAフォークとの互換性が不明）は解消**している。
`v0.3-branch+dya` に留まっていたら逆に使えなかった可能性が高く、今回の v0.4 移行が
そのまま前提条件を満たした形。

### 試験ビルド結果（2026-08-12、コミット `115914a`）— **成功**

`config/west.yml` に `eswai/zmk-naginata@316bcb5b76b5` を追加し、keymap へは
組み込まない状態でビルド → **3ビルドすべて success**。

**この結果が何を証明していて、何を証明していないか**（ここは正確に扱うこと）:

- ✅ **薙刀式の C ソースは実際にコンパイルされている**。モジュールの
  `CMakeLists.txt` は `CONFIG_NAGINATA AND (NOT CONFIG_ZMK_SPLIT OR
  CONFIG_ZMK_SPLIT_ROLE_CENTRAL)` で `target_sources` するので、中央側＝右手
  ビルドで4ソースすべてが対象。`CONFIG_NAGINATA` は既定 `y`。
  → **ZMK v0.4 / Zephyr 4.1 上での API 互換性は実証された**。
  v0.3 に留まっていたら、ここで落ちていた可能性が高い
- ❌ **フラッシュ消費はまだ測れていない**。`DT_INST_FOREACH_STATUS_OKAY` により
  デバイス実体は DT ノードがある時だけ生成され、behavior ノードは
  `/omit-if-no-ref/` なので `&ng` を参照するまで生成されない。結果、
  リンカに gc-sections で回収されて**成果物サイズはほぼ変化なし**
  （mona2_r: 295,149 B ≒ 導入前と同等）。実際の消費は keymap へ組み込んでから測る

### 残っている確認事項（着手時にやること）

1. ~~試験ビルド~~ → **完了（上記）**
2. `zmk-module-runtime-input-processor` との入力処理パイプライン競合の有無
3. **ランタイムコンボとの衝突**（v0.3 時代には無かった新論点）:
   `cormoran,runtime-combo-defaults` のコンボ判定と薙刀式の同時打鍵ロジックが
   同じキーイベントを取り合わないか。現行8スロットのうち特に
   `S`+`D`(Tab) / `D`+`F`(Shift+Tab) / `J`+`K`・`K`+`L`(コピペ) は薙刀式の
   打鍵範囲と重なるため、薙刀レイヤーでは無効化する設計が要る
4. 案A（大西配列の `&tog` オーバーレイ）についても、コンボ暴発問題が
   ランタイムコンボ移行でどう変わるか整理する

> なお `eswai` 氏は macOS / Windows / Linux 版の薙刀式実装も公開しているので、
> OS 側実装（案D）との比較検討にも使える。

---

## 0. Release の公開（実機確認後に実施）

**決定日**: 2026-08-12

`.github/workflows/release.yml` は作業ブランチに用意済み。ただし GitHub は
**デフォルトブランチに存在するワークフローしか `workflow_dispatch` を受け付けない**
ため、`main` にマージするまで手動実行できない（タグ push トリガーは使える）。

**方針**: お盆明けに実機で動作確認 → ファーム移行ごと `main` へマージ →
タグ `v1.0.0-rc1` で Release を切る。ワークフローはタグ名にハイフンが含まれると
自動でプレリリース扱いにする。

それまでの間、ファームは Actions の実行ページの Artifacts から入手できる
（`artifact-mona2_r` / `artifact-mona2_l` / `artifact-settings_reset`、保持90日）。

---

## 3. ブランチの整理

**依頼日**: 2026-08-12

**質問**: 「あるべき姿は main と作業中ブランチのみ、という理解で合っているか。
GitHub 上で Windows のフォルダのように `old/` へまとめておくことはできないか」

**回答**: 認識は正しい。ただし Git のブランチはフォルダではなく**コミットへの
ポインタ**なので、「しまっておく」概念が無い。`old/xxx` という名前のブランチは
作れる（`/` はただの文字）が整理にはならない。代わりに**タグ**が正しい退避手段で、
消す前にタグを打てば履歴は永久に残り、ブランチ一覧だけ綺麗になる。

### 実行状況（2026-08-13）

Claude Code の実行環境からは**リモートブランチを削除できなかった**。10本すべて
`fatal: the remote end hung up unexpectedly`。この環境の git プロキシが ref の
削除・作成を通さない（fast-forward 更新のみ許可）ため。タグ push が通らないのと
同じ症状。**削除は手元の環境で実行すること。**

### 削除して問題ないもの（8本）

| ブランチ | 判断根拠 |
|---|---|
| `claude/click-layer` | main にマージ済み |
| `claude/keymap-rework` | main にマージ済み |
| `claude/mona2-firmware-review-s2s0vk` | main にマージ済み |
| `claude/pan-aml-tuning` | main にマージ済み |
| `claude/repo-main-review-5vuajq` | main にマージ済み |
| `claude/snap-4dir-doc` | 未マージだが内容は CHANGELOG 2026-06-21 の項として main に入っており実質重複 |
| `claude/japanese-text-check-3gAgC` | 未マージだが2コミットとも `[Draw]` の自動生成物のみ。メッセージに "8方向化" とあるのは元コミットの文言の引き写しで、実装は含まれない |
| `DYA-Studio` | `DYA-ooshini` に内包されるため、そちらを残せば失われない |

```bash
git fetch --prune origin
for b in claude/click-layer claude/keymap-rework \
         claude/mona2-firmware-review-s2s0vk claude/pan-aml-tuning \
         claude/repo-main-review-5vuajq claude/snap-4dir-doc \
         claude/japanese-text-check-3gAgC DYA-Studio; do
  git push origin --delete "$b"
done
```

### 判断保留（2本）— 消す前に中身を見る価値がある

- **`DYA-ooshini`（27コミット）**: 名前の "ooshini" は**大西配列**を指すと思われ、
  上の項目2（薙刀式）と地続きの可能性がある。`DYA-Studio`(25) を内包する
- **`hhkb-research`（6コミット）**: moNa2 とは無関係だが、HHKB のファームウェア解析
  （STM32 Cortex-M / `.hfb` フォーマット / 実機での 0xD0 検証）という**独立した調査成果**。
  消すと再現に手間がかかる種類のもの

消すと決めた場合は、先にタグへ退避してから:

```bash
git tag archive/DYA-ooshini   origin/DYA-ooshini
git tag archive/hhkb-research origin/hhkb-research
git push origin archive/DYA-ooshini archive/hhkb-research
git push origin --delete DYA-ooshini
git push origin --delete hhkb-research
```

戻すときは `git checkout -b <名前> archive/<名前>`。

### ローカルの残骸掃除

```bash
git fetch --prune origin
git branch -vv | grep ': gone]' | awk '{print $1}' | xargs -r git branch -D
```

---

## 4. レイヤー・キーマップを PC 画面に表示するアプリ

**依頼日**: 2026-08-12（以前にも相談あり）/ 本人の希望: 再開したい

現在アクティブなレイヤーとそのキーマップを PC 上にリアルタイム表示するアプリ。
着手時に、あらためて要件（対応OS・常駐方法・レイヤー情報の取得経路）から相談する。

- 取得経路の候補が v0.4 移行で増えている可能性がある。`zmk-feature-input-stream`
  （キー押下のライブ表示）や custom Studio RPC 経由でレイヤー状態を取れるなら、
  以前検討したときより実装が楽になっているかもしれない。ここは要調査
