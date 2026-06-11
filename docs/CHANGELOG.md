# 変更履歴

このファイルはキーマップ設計・ドキュメントへの変更を記録します。
実装ファイル（`.keymap` / `.overlay` / `.conf`）の変更はコミットログを参照してください。

フォーマット：
```
## YYYY-MM-DD  タイトル
- 変更内容（by GitHub 編集 / by チャット依頼）
```

---

## 2026-06-11  ゼロベースレビューに基づく修正・改善

（by チャット依頼）

### バグ修正
- **コンボの `layers` プロパティを復元**: keymap-editor のコミット（211da6f）が全コンボの `layers` を削除し、Mac/Win のコピペ分岐（J+K / K+L）が機能していなかった。Tab / Shift+Tab / 英数+かな も全レイヤーで発火する状態だった。
  - `combo_tab` / `combo_stab`: `layers = <WIN MAC>`（復元）
  - `combo_esc_ble`: `layers = <WIN MAC O24>`（O24 トグル中も BLE 層へ入れるよう改善）
  - コピペ 4 コンボ: `layers = <MAC>` / `<WIN>`（復元）
  - `combo_toO24`: `layers = <MAC WIN O24>`（新規。機能層での Q+P 誤爆を防止）
- `bt_mac0` マクロを `&to 0` → `&to MAC` に復元（keymap-editor 起因の劣化）
- `.github/workflows/no build.yml` を削除（名前に反して有効で、build.yml と同一ビルドを毎 push 二重実行していた）

### 改善
- mod-tap 誤爆対策: `&mt` / `mt_bspc` に `require-prior-idle-ms = <125>` を追加。`config/mona2.keymap` 冒頭の `MT_REQUIRE_PRIOR_IDLE_MS` で調整・無効化（0）が可能
- `config/west.yml`: 浮動 `main` だった 4 モジュール（battery-history / settings-rpc / runtime-sensor-rotate / input-processor-keybind）を 2026-06-11 時点の HEAD SHA に pin
- `draw.yml`: 存在しない `config/mona2.dtsi` のパス参照を `boards/shields/mona2/mona2.dtsi` に修正、draw-jis ジョブの push 前に `git pull --rebase` を追加

### ドキュメント
- README.md のレイヤー表を現行番号（O24=2, SYM=3, …, CURSOR=12）に修正
- docs/keymap-phase1.md: `inertial-scroll-decay-pct` 97→93、PAN の `zip_scroll_scaler 1 5`→`1 4`、`zip_mouse_gesture_win` の定義場所（mona2.dtsi）を実装に一致させ、コンボ layers / require-prior-idle-ms / 追加 pin の記述を追加

---

## 2026-06-10  O24 バグ修正 & レイヤー番号再編

（by チャット依頼）

- O24 レイヤーを layer 12 → layer 2 に移動（layer 12 では SYM/NUM/NAV より優先度が高くなり機能不全になる ZMK 仕様の問題を修正）
- O24 T位置キーバインドを `COMMA` → `DOT` に修正（コンマが2つ並んでいた誤りを解消）
- `mona2_r.overlay` の全レイヤー番号参照を新番号に更新（AML=7、scroller=4,5,6、panner=9、gesturer_mac=10、gesturer_win=11）
- `keymap-drawer/mona2.yaml` の O24 セクションを WIN の直後に移動し、T位置エントリを `','` → `'.'` に修正
- `docs/keymap-phase1.md` のレイヤー表・AML/慣性スクロール節・コードブロックを新番号に合わせて更新

---

## 2026-06-10  ドキュメント最新化（実装との乖離修正・README2.md 廃止）

（by チャット依頼）

### README.md
- Layer 表 行9・10 の起動方法を修正: `Del 長押し` → `Q 長押し`
- Layer 表 行11 CURSOR の起動方法を修正: `Q 長押し（誤）` → `未実装（予約済み）`
- Layer 12 O24（`Q`+`P` トグル）を Layer 表に追加
- トラックボール機能表を修正: Q長押し→ウィンドウスナップ、Del 行を削除
- ウィンドウスナップ節の操作キーを修正: `Del` → `Q`
- DYA Studio セクションのリンク先を `README2.md` → `docs/keymap-phase1.md` に変更
- `boards/shields/mona2/mona2.keymap` が旧デフォルトである旨の補足を末尾に追加

### docs/keymap-phase1.md
- 冒頭のブランチ名記述（`claude/keymap-rework`）を削除し「設計・実装ドキュメント」に変更
- Layer 表に Layer 11（CURSOR、未実装）・Layer 12（O24）を追加
- `inertial-scroll-threshold` の値を修正: `<4>` → `<8>`（`mona2_r.overlay` と一致）
- Phase 2 共通前提の Layer 番号記述を修正: `0〜10` → Layer 11/12 が実装済みの実態に合わせる

### README2.md
- `old/README2.md` に移動（廃止）。内容は `docs/keymap-phase1.md` に包含済み。
