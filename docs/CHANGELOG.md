# 変更履歴

このファイルはキーマップ設計・ドキュメントへの変更を記録します。
実装ファイル（`.keymap` / `.overlay` / `.conf`）の変更はコミットログを参照してください。

フォーマット：
```
## YYYY-MM-DD  タイトル
- 変更内容（by GitHub 編集 / by チャット依頼）
```

---

## 2026-06-21  四隅スナップ不発火を既知の制限としてドキュメント化

（by チャット依頼）

- **根本原因**: `kot149/zmk-mouse-gesture` の `detect_direction()` が `abs(x) > abs(y)` で常に1方向を選択し斜め合成値を返さない。`direction_to_index()` が `GESTURE_UP_LEFT`(=5) 等を `-1` 判定して trie 構築時に黙って破棄するため、四隅パターンが永続的に発火しない。
- `README.md`: スナップ表から四隅4行（↖↗↙↘）を削除し、「モジュールが4方向のみ認識するため発火しない（既知の制限）」注記を追加。
- `docs/keymap-phase1.md`: GESTURE SNAP節に四隅未対応の注記追加。また `suppress-movement` の記述を現行実装（`zip_xy_to_scroll_mapper` + `zip_scroll_scaler 0 1` による REL→WHEEL 型変換）に更新。
- `config/mona2.keymap`: Mac/Win 両方の四隅パターン群に「現状発火しない（将来対応時に備えて残置）」コメントを追加。

---

## 2026-06-21  クリック層(CLICK=13)を追加（AMLと共存）

（by チャット依頼）

### 目的
クリック（MB1/2/3）は従来 MOUSE層(7) にあり、AML（ボール操作で自動遷移・500ms静止で復帰）経由でしか使えなかった。ボールを止めると復帰してしまい狙ってクリックしづらい。AMLは維持したまま、キー長押しで明示的にクリック層へ入れるようにした。

### 追加内容
- **CLICK層(13)** を新設（`config/mona2.keymap`）。両手にクリッククラスタを配置:
  - 左手 S/D/F = 左/中/右クリック、X/V = 戻る(MB4)/進む(MB5)
  - 右手 J/K/L = 左/中/右クリック、M/. = 戻る(MB4)/進む(MB5)（MOUSE層と同じ）
- **起動キーを2つ**用意（タップ時は元の機能を維持）:
  - DEL（右手）→ `&lt CLICK DEL`（タップ=DEL）
  - 「Bの一つ右」= caps_word の位置（左手最内）→ カスタム hold-tap `clk_caps`（タップ=caps_word）
  - 片手で起動し、もう片方の手でクリックできる
- **AMLと独立して共存**: CLICK層は trackball listener のどのサブノードにも含めないため、層中もボール入力はデフォルトチェーンを通りカーソルは普通に動く。クリックは層13自身の `&mkp` が供給するのでAMLの発火/タイムアウトに依存しない
- LED配色: CLICK=白（`config/mona2_r.conf`、`LAYER_13_COLOR=7`）
- CURSOR(12) は予約のまま据え置き

---

## 2026-06-15  PAN スクロール量 3 倍 & AML 発火閾値の調整

（by チャット依頼）

### PAN（P長押し）のスクロール量を 3 倍に
- panner の `zip_scroll_scaler` を `1 5`（1/5）→ `3 5`（3/5）に変更（`boards/shields/mona2/mona2_r.overlay`）。広範囲をざっと移動する用途のため。scroller（NAV 層スクロール）は従来どおり据え置き

### AML 誤発火（タイピング中の振動）対策
- `&zip_temp_layer` の `require-prior-idle-ms` を `300` → `500` に増加（`boards/shields/mona2/mona2_r.overlay`）。打鍵直後 500ms 間はトラックボールが動いても MOUSE 層へ移行しないため、タイピング中の振動による誤発火を抑制。効きが弱ければ 600〜700ms へ追加調整可能

---

## 2026-06-15  Q長押しスナップ中のカーソル移動問題を修正

（by チャット依頼）

### バグ修正（Q長押し中にカーソルが動く問題）

- **根本原因**: `suppress-movement` が `ZMK_INPUT_PROC_STOP` を返してもカーソル移動が止まらない DYA fork の挙動が原因。PAN（P長押し）はカーソルが止まるがそれは `suppress-movement` のためではなく、チェーン内の `zip_xy_to_scroll_mapper` が REL_X/Y イベントを WHEEL/HWHEEL に型変換するため HID 側でカーソル移動として解釈されないため。SNAP チェーンにはこの型変換がなく REL_X/Y がそのままカーソルを動かしていた。
- **修正**: `gesturer_mac` / `gesturer_win` の `input-processors` にジェスチャープロセッサの**後ろ**に `&zip_xy_to_scroll_mapper` と `&zip_scroll_scaler 0 1` を追加（`boards/shields/mona2/mona2_r.overlay`）。ジェスチャープロセッサはイベントを async キューに積んでから return するため、後続の型変換はジェスチャー認識に影響しない。
  - `zip_xy_to_scroll_mapper`: REL_X/Y → WHEEL/HWHEEL に型変換（カーソル移動しなくなる）
  - `zip_scroll_scaler 0 1`: スクロール値を 0 にして意図しないスクロールを防ぐ
- `suppress-movement` を `&zip_mouse_gesture` / `&zip_mouse_gesture_win` から削除（型変換で不要になった）（`config/mona2.keymap`）

---

## 2026-06-12  LED レイヤー配色の整理

（by チャット依頼）

- rgbled-widget のレイヤー色をデフォルト任せから明示的な配色に変更（`config/mona2_r.conf`）
  - ベース層 MAC / WIN / O24 = 消灯（WIN・O24 が常時点灯してしまう問題の解消）
  - SYM=緑 / NUM=青 / NAV-M・NAV-W=シアン / MOUSE=白 / BLE=赤(橙に見える) / PAN=黄 / SNAP-M・SNAP-W=マゼンタ
- docs/keymap-phase1.md に LED 配色表の節を追加

---

## 2026-06-11  ウィンドウスナップ ジェスチャー不発火の修正 & センサー感度アップ

（by チャット依頼）

### バグ修正（Q長押しスナップが発動せず、カーソルがX反転で動く問題）
- 原因1: kot149 ジェスチャープロセッサは既定で「起動キー（`&mouse_gesture` 等）押下中のみアクティブ」仕様。本構成は `&lt` レイヤー起動のため常に非アクティブ → イベント素通り。`&zip_mouse_gesture` / `&zip_mouse_gesture_win` に **`always-active`** を追加して解消
- 原因2: gesturer チェーンに X 反転補正が無く、素通りしたイベントが X 反転のままカーソルを動かしていた。`gesturer_mac` / `gesturer_win` に **`zip_xy_transform INPUT_TRANSFORM_X_INVERT`** を追加（ストローク左右判定の正常化も兼ねる）
- **`suppress-movement`** を追加し、ジェスチャー認識中はカーソルが動かないように（MX Ergo 的挙動）

### センサー感度アップ（cpi 600→800）と連動補正
- `zip_scroll_scaler` 1/4→1/5（scroller / panner。スクロール体感速度を維持）
- `inertial-scroll-threshold` 8→10（慣性の余韻長を維持）
- `stroke-size` 150→200（ジェスチャーの物理フリック距離を維持）

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
