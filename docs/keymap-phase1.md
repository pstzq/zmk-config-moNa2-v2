# moNa2 キーマップ — Phase 1 実装まとめ

> このドキュメントは `claude/keymap-rework` ブランチで実装した内容のまとめです。
> **キーマップ図**は GitHub Actions(`draw.yml`)が push 毎に自動生成（2種類）：
> - US(ANSI)準拠: [`keymap-drawer/mona2.svg`](../keymap-drawer/mona2.svg)（keymap-drawer標準。記号は `Sft+1` `[` 等のUS表記）
> - **JIS準拠**: [`keymap-drawer/mona2_jis.svg`](../keymap-drawer/mona2_jis.svg)（`scripts/jis_relabel.py` で JIS で実際に出る記号 `@ : ^ ¥` 等に変換した版）

## 目的
- 日本語(JIS)環境での **US/JIS 記号の読み替えの煩雑さ** を恒久的に解消する。
- Mac / Windows 併用での差分を整理する。
- トラックボール体験の向上（ジェスチャー・慣性スクロール）。

## 前提
- OS側キーボード配列は **Mac・Windows とも JIS** で統一運用。
- Mac=標準IME / Windows=Google日本語入力。
- **DYA Studio**（ZMK Studio系GUI）対応。
- 対象: moNa2（右手トラックボール、左手ロータリーエンコーダ）。

## 設計の2軸
| 軸 | 課題 | 解 |
|---|---|---|
| 軸A: OS差分 | 修飾キー(Ctrl↔⌘)等 | ベース層のみ WIN/MAC を分離、機能層は共有。OS切替は BTプロファイル連動 |
| 軸B: JIS記号 | `@ : ^` 等のズレ | `config/jis.h` を整備し、記号は全てこれ経由で記述 |

---

## レイヤー構成
| # | 名称 | 起動方法 | 内容 |
|---|---|---|---|
| 0 | MAC | 既定 | QWERTY。修飾キー=Mac系(⌘/Ctrl/⌥) |
| 1 | WIN | BTプロファイル連動(BT1/BT2) | QWERTY。修飾キー=Windows系(Ctrl/Win/Alt) |
| 2 | SYM 記号 | Space 長押し | JIS正準の記号一式（`jis.h`経由） |
| 3 | NUM 数字 | Enter 長押し | 右手テンキー＋左手F1〜F12 |
| 4 | NAV-M 矢印(Mac) | 英数 or かな 長押し（MACベース時） | 左手 逆T字＋Home/End/PgUp/PgDn。右手矢印IJKL/メディア/輝度 |
| 5 | NAV-W 矢印(Win) | 英数 or かな 長押し（WINベース時） | 左手 逆T字＋Home/End/PgUp/PgDn。右手矢印IJKL/メディア/輝度 |
| 6 | MOUSE | オートマウス(AML) ＝ボール操作で自動 | 右手にマウスボタン |
| 7 | BLE/設定 | 英数 ＆ かな 同時押し(コンボ) | Bluetooth/出力/Studio/Boot のみ |
| 8 | GESTURE PAN | P 長押し | 2D自由スクロール（パン） |
| 9 | GESTURE SNAP (Mac) | Del 長押し（MACベース時） | ウィンドウスナップ（Rectangle） |
| 10 | GESTURE SNAP (Win) | Del 長押し（WINベース時） | ウィンドウスナップ（Win+矢印） |

---

## 各レイヤー詳細

### Base (WIN / MAC)
- 英字 QWERTY。両OSで英字・機能層アクセスは共通、**違いは修飾キーのみ**。
  - MAC: `⌘(GUI) / Ctrl / ⌥(Alt)`、BS長押し=⌘、長音ー長押し=⌘
  - WIN: `Ctrl / Win(GUI) / Alt`、BS長押し=Ctrl、長音ー長押し=Ctrl
- `Z` = mod-tap Shift（`&mt LSHFT Z`）
- `L` の右隣 = **長音「ー」**（`JIS_MINUS`、hold=Ctrl/⌘）
- **Backspace** は専用 hold-tap `mt_bspc`（`quick-tap-ms=200`）。タップ→すぐ長押しで **BS をオートリピート**（連続削除）。修飾キー(⌘/Ctrl)の hold はそのまま。他の mod-tap には quick-tap を付けていない。
- **P** = `&lt GESTURE_PAN P`（tap=P / hold=パンモード）
- **Del** = `&lt GESTURE_SNAP_MAC DEL` または `&lt GESTURE_SNAP_WIN DEL`（tap=Del / hold=スナップモード。OSベース層に応じて自動分岐）

### 親指クラスタ
| | 左手 | | | 右手 | |
|---|---|---|---|---|---|
| | BS | Space | 英数(LANG2) | かな(LANG1) | Enter |
| tap | Backspace | Space | 英数(LANG2) | かな(LANG1) | Enter |
| hold | Ctrl/⌘ | **SYM** | **NAV** | **NAV** | **NUM** |

- 英数・かな は**どちらの長押しでも NAV**（OS別に NAV-M / NAV-W 自動）。
- **英数 ＆ かな 同時押し → BLE**（コンボ。タップ同時は Esc）。
- NUM は Enter 長押しへ移動（左手 F1〜F12＋右手テンキーが使える）。

### 中央3キー（一等地）
- 左内側 = **Caps Word**（`&caps_word`／1単語だけ大文字）
- 右内側・上 = **`@`**（`JIS_AT`／Teams等のメンションで多用するため表に直置き）
- 右内側・中 = **`_`**（`JIS_UNDER`／アンダースコア直置き）
- ※ Repeat(`&key_repeat`)は使用頻度が低かったため廃止
- ※ `;` `:` は記号層にあるため基底中央には置かない

### コンボ（sayu-hub 意識）
| コンボ | 動作 |
|---|---|
| `S`+`D` | Tab |
| `D`+`F` | Shift+Tab |
| `英数`+`かな` | tap=Esc / hold=BLE層 |
| `J`+`K` | コピー（MAC=⌘C / WIN=CtrlC、OS別に分岐） |
| `K`+`L` | ペースト（MAC=⌘V / WIN=CtrlV、OS別に分岐） |
- コピペは `layers = <MAC>` / `<WIN>` で同位置コンボを2本ずつ定義し、ベース層に応じて修飾を自動で出し分け。

### SYM（記号）
- `config/jis.h` のエイリアスで JIS-OS でも記号が正しく出る。
```
上段:  !  "  #  $  %        &  '  (  )  |
中段:  ^  ~  +  -  *    ¥   {  }  [  ]    =
下段:  1  2  3  4  5   ; :  6  7  8  9    0
```
- 上段: 数字段の Shift 面 `! " # $ %` / `& ' ( ) |`。`|` は P 位置に1つ。
- 中段（ホーム行）: 左 `^ ~ + - *` / 中央 `` ` `` / 右 `{ } [ ]` ＋ `=`（ー位置）。演算子・括弧を集約。
- 下段: 数字 `1〜5` / 中央 `; :`（左がセミコロン）/ `6〜0`。SYM 内で数字直打ちが可能。
- `< > ?` は SYM に持たず、ベース層の `, . /` ＋ Shift で出す割り切り。
- `\`（バックスラッシュ）は **JIS では入力にクセがあり、`¥`（中央 `JIS_YEN`）がその役割を兼ねる**ため別途配置不要。`_` はベース層中央に常設。
- バッククォート（`` ` ``）は元々 SYM 中央にあったが、Shift+@ で代替できるため `¥` に置き換え。

### NUM（数字・右手テンキー＋左手F1〜F12）
```
左手 F1-F12                   右手テンキー
F1   F2   F3   F4   F5        *  7  8  9  /
F6   F7   F8   F9   F10       +  4  5  6  -
F11  F12  —    —    —         0  1  2  3  .
```
- テンキーHID（`KP_*`）なので配列に依存しない。0 は 1 の左。
- 左手は **F1〜F12**（旧 BLE 層から移設）。元の矢印/Tab/BS/Del は NAV・ベース層と重複していたため整理。

### NAV-W / NAV-M（矢印・左手）
- 共通: `E=↑`, `S/D/F=←↓→`（逆T字）, `A=Home`, `G=End`, `X=PgUp`, `C=PgDn`。
- `Z` 位置に**単体 Shift**（`&kp LSHFT`）。矢印と組み合わせて範囲選択（Shift+矢印）に。
- 右手にも矢印（**I/J/K/L** 位置）を配置：`I=↑`, `J=←`, `K=↓`, `L=→`（逆T字）。
- OS 別キー:
  | キー位置 | NAV-W (Windows) | NAV-M (Mac) |
  |---|---|---|
  | `T` | Win+Tab（タスクビュー） | Ctrl+↑（Mission Control） |
  | `P` | PrintScreen（全画面） | ⌘⇧3（全画面） |
  | `O` | Win+Shift+S（範囲指定） | ⌘⇧4（範囲指定） |
  | `U` | Alt+PrintScreen（アクティブ窓） | `ss_window_mac`＝⌘⇧4→Space（ウィンドウ単位） |
- **Mute** は `H`（右手ホーム内側）に `C_MUTE`（音量±の真上）。両 NAV 共通。
- 右手下段メディア・輝度キー（両 NAV 共通）: `M / , / .` ＝ `⏮ ⏯ ⏭`（`C_PREV / C_PP / C_NEXT`）、両端 `N / /` ＝ `🔅 🔆`（`C_BRI_DN / C_BRI_UP`）。
- **ロータリーエンコーダ（左ノブ）は `rsr_vol` で音量調整**（NAV/BLE 層のみ）。その他の層ではスクロール。

### MOUSE（オートマウスレイヤー）
- 右手に `LCLK / RCLK / MCLK / MB4(戻) / MB5(進)`。
- トラックボール操作で MOUSE 層(=6)へ自動遷移（AML）。

### BLE/設定（Bluetooth・端末管理に限定）
- **雑多なキーは置かず Bluetooth まわりに集中**：BT0〜BT4 の選択（Y〜P 位置）。
  - BT0=Mac / BT1=Win / BT2=Win はマクロでレイヤー自動切替付き。
  - **BT3 / BT4 はプロファイル切替のみ**（層は手動で合わせる）。
- 端末管理: `OUT`(USB/BLE出力切替)、`Studio`(`&studio_unlock`)、`Boot`(`&bootloader`)。
- F1〜F12 は **NUM 層左手**へ、メディアキーは **NAV 層右手**へ移設済み。
- エンコーダは `rsr_vol`（音量）に切り替わる。

### GESTURE PAN（P長押し・層8）
- トラックボールで **縦横自由にスクロール**（2Dパン）。
- `zip_xy_to_scroll_mapper` → `zip_scroll_scaler 1 4` で速度調整（通常スクロール `1 5` よりわずかに速め）。
- キー入力はすべて `&trans` で素通り。

### GESTURE SNAP（Del長押し・層9/10）
- トラックボールをストロークするとウィンドウをスナップ。
- `stroke-size = <150>`、`enable-eager-mode`、`gesture-cooldown-ms = <200>`。

| ストローク | Mac（Rectangle） | Windows |
|---|---|---|
| ← | 左半分 `Ctrl+Opt+←` | 左半分 `Win+←` |
| → | 右半分 `Ctrl+Opt+→` | 右半分 `Win+→` |
| ↑ | 最大化 `Ctrl+Opt+Enter` | 最大化 `Win+↑` |
| ↓ | 中央/1/2 `Ctrl+Opt+C` | 元に戻す `Win+↓` |

---

## OS切替（BTプロファイル連動）
- マクロ `bt_mac0` / `bt_win1` / `bt_win2` が「ベース層切替(`&to`)＋`&bt BT_SEL`」をまとめて実行。
  - BT0 → MAC ベース、BT1/BT2 → WIN ベース。
  - BT3/BT4 は `&bt BT_SEL` のみ（ベース層の自動切替なし。必要なら BLE 層でマクロ追加）。
- デフォルト(電源投入時)は MAC ベース（layer 0）。

## オートマウスレイヤー(AML)
- `boards/shields/mona2/mona2_r.overlay` のトラックボール listener に `&zip_temp_layer 6 500` を配線。
- ボール操作で MOUSE 層(=6) へ自動遷移、500ms 操作なしで復帰。
- `require-prior-idle-ms = <300>` でタイピング直後の誤AML発動を防止。
- ボールスクロールのトリガは NUM(=3) / NAV_MAC(=4) / NAV_WIN(=5)（`layers = <3 4 5>`）。

## 慣性スクロール（razilyis フォーク）
- `badjeff/zmk-pmw3610-driver` の代わりに **`razilyis/zmk-pmw3610-driver`**（`Dev-v0.3_inertial-scroll` ブランチ）を使用。
- 参考: [note 記事](https://note.com/razily/n/nea1575614710)
- NUM / NAV_MAC / NAV_WIN 層（`inertial-scroll-layers = <3 4 5>`）でスクロール後に慣性が効く。
- 主な設定値（`mona2_r.overlay` の `trackball_central@0` ノード内）:
  ```dts
  inertial-scroll;
  inertial-scroll-layers = <3 4 5>;
  inertial-scroll-gain-pct = <130>;   // 指を離した瞬間の初速の強さ
  inertial-scroll-decay-pct = <99>;   // 1回ごとの速度残存率(%)
  inertial-scroll-interval-ms = <10>; // 慣性更新周期(ms)
  inertial-scroll-threshold = <4>;    // 停止判定の下限値
  ```
- **元に戻す場合**: `west.yml` の `razilyis` エントリをコメントアウトして `badjeff` エントリを復活させ、`mona2_r.overlay` の `inertial-scroll*` 行をコメントアウトするだけ（2ファイル、数行の変更）。

## マウスジェスチャー（実装済み）
- モジュール: **`kot149/zmk-mouse-gesture`**（`855a6e80...` SHA で pin）。
- DYAフォーク（`cormoran/zmk v0.3-branch+dya`）との互換性確認済み（CI 通過）。

### 入力プロセッサ配線（`mona2_r.overlay`）
```dts
&trackball_central_listener {
    // デフォルト: カーソル移動 + AML(layer 6)
    input-processors = <&zip_xy_transform INPUT_TRANSFORM_X_INVERT
                        &mouse_runtime_input_processor
                        &zip_temp_layer 6 500>;

    scroller {        // NUM/NAV 層: スクロール
        layers = <3 4 5>;
        input-processors = <...zip_xy_to_scroll_mapper... &zip_scroll_scaler 1 5>;
    };

    panner {          // GESTURE_PAN(8): 2D スクロール
        layers = <8>;
        input-processors = <...zip_xy_to_scroll_mapper... &zip_scroll_scaler 1 4>;
    };

    gesturer_mac {    // GESTURE_SNAP_MAC(9): Rectangle スナップ
        layers = <9>;
        input-processors = <&zip_mouse_gesture>;
    };

    gesturer_win {    // GESTURE_SNAP_WIN(10): Win スナップ
        layers = <10>;
        input-processors = <&zip_mouse_gesture_win>;
    };
};
```

### Mac / Win 分離の理由
- Mac: Rectangle の `Ctrl+Opt+矢印` / Win: OS標準 `Win+矢印` でショートカットが異なる。
- 層を分けることでベース層（MAC/WIN）に応じて `&lt` が自動で正しい層を起動する。
- `zip_mouse_gesture_win` は Mac 版と同一ノード型だが別インスタンスとして `mona2_r.overlay`（および `mona2_l.overlay`）に定義。左側ビルド時にも `mona2.keymap` からの参照が解決できるよう両 overlay に定義を配置している。

## 依存モジュールのpin（重要）
DYAモジュールの `revision: main` が浮動で、`zmk-module-runtime-input-processor` が **2026-04-30 に zmk v4 へ移行** → fork(`v0.3-branch+dya`)と非互換になりビルド失敗(`too many arguments to zmk_keymap_layer_activate`)。shakupan版に倣い `config/west.yml` で v4移行前にpin：
- `zmk-module-runtime-input-processor`: `main` → `dbf92f7`
- `zmk-module-ble-management`: `main` → `851661c`
- `zmk-mouse-gesture`: `main` なし → `855a6e80f18f4b19ea2181648ac062ec72876ece`（masterブランチHEAD）

---

## ビルド & 書き込み
- push すると GitHub Actions(`build.yml`)が uf2 を生成。実行ページ下部の Artifacts `firmware` をDL。
- 含まれる uf2: `mona2_l` / `mona2_r` / `settings_reset`。
- **キーマップ構造が大きく変わったため、初回は `settings_reset` も一度書き込む**ことを推奨（旧設定の残留防止）。

---

## Phase 2（今後の検討）

### 大西配列・薙刀式 導入案（実装優先度: 低）

**共通前提**
- OS側配列は引き続き JIS 固定。
- 現状のレイヤー番号 0〜10 は変更しない。追加は 11 番以降。
- BLE層からの切替ボタンとして実装する想定。

#### 案 A: `&tog` オーバーレイ方式（大西配列向き・最小コスト）

- 大西配列レイヤー（例: 11）を MAC/WIN の上に重ねる透過レイヤーとして追加。
- 英字キー位置のみ上書き。SYM / NAV / NUM / BLE は `&trans` で素通り。
- BLE層に `&tog 11` ボタン1つで オン/オフ。
- **電源再投入で QWERTY に戻らない**（ZMK はデフォルトで `&tog` 状態をフラッシュ保存）。BLE層に「QWERTY 戻し `&to MAC`」を必ず用意すること。
- 薙刀式には**不向き**（同時打鍵が単純なレイヤー置換では実現できない）。

#### 案 B: `&to` ベース層追加方式（大西・薙刀どちらでも適用可）

- 大西MAC / 大西WIN などの新ベース層を追加。
- BTプロファイル連動マクロ（`bt_mac0` 等）も対応する配列を考慮して拡張が必要。
- **電源再投入では戻らない**ため、BLE層の「QWERTY戻り」ボタンは必須。

#### 案 C: `zmk-naginata` モジュール方式（薙刀式の本格対応）

- 外部モジュール（例: `nickcoutsos/zmk-naginata`）を `config/west.yml` に追加。
- 薙刀式の同時打鍵ロジックをモジュールが処理。
- **要確認**: DYAフォーク（`v0.3-branch+dya`）との互換性。最初は keymap への組み込みなしでビルドが通るかだけ確認する。
- `west.yml` 追加時は `revision: main` のまま放置せず、ビルドが通った時点の SHA に pin すること。

#### 案 D: OS側IME委託方式（ゼロ実装）

- キーボード側は現状のまま変更なし。OS側のIME（かわせみ3・AquaSKK・ATOK等）に配列変換を任せる。
- 接続先デバイスごとにIME設定が必要。

#### 実装前に潰すべき障壁（案A）
- **既存コンボが大西配列で暴発する**: コンボは物理キー番号で登録されているため、大西配列で文字位置が変わるとコンボが誤発火する。大西配列レイヤー定義時に `layers = <MAC WIN>` から外すか、別コンボを追加すること。

#### 実装前に潰すべき障壁（案C）
- **ZMK フォーク互換性**: `zmk-naginata` は標準 ZMK を前提に開発されており、`cormoran/zmk v0.3-branch+dya` で動くかは事前ビルド検証が必須。
- **モジュール競合リスク**: `zmk-module-runtime-input-processor` との入力処理パイプライン競合の可能性。

---

### その他の検討事項
- ホームローMod 本格導入（閾値チューニング込み）
- LANG切替の `eager_tap_dance` 方式（kot版）併存
- BT3/BT4 に OS連動マクロを追加（現在はプロファイル切替のみ）
- roBaへの横展開

---

## 参考リソース

| リソース | 用途 |
|---|---|
| [DYA Studio](https://studio.dya.cormoran.works/) | GUI でキーマップ編集（ZMK Studio 系） |
| [cormoran/zmk](https://github.com/cormoran/zmk) `v0.3-branch+dya` | ZMK 本体フォーク（DYA Studio 対応） |
| [badjeff/zmk-pmw3610-driver](https://github.com/badjeff/zmk-pmw3610-driver) | PMW3610 トラックボールドライバ（慣性スクロール無効版） |
| [razilyis/zmk-pmw3610-driver](https://github.com/razilyis/zmk-pmw3610-driver) `Dev-v0.3_inertial-scroll` | PMW3610 トラックボールドライバ（慣性スクロール対応フォーク） |
| [cormoran/zmk-module-runtime-input-processor](https://github.com/cormoran/zmk-module-runtime-input-processor) `dbf92f7` | 入力処理パイプライン拡張（v4移行前にpin） |
| [cormoran/zmk-behavior-runtime-sensor-rotate](https://github.com/cormoran/zmk-behavior-runtime-sensor-rotate) | エンコーダを DYA Studio から動的変更可能にする |
| [caksoylar/zmk-rgbled-widget](https://github.com/caksoylar/zmk-rgbled-widget) `v0.3-branch` | RGB LED ウィジェット |
| [zettaface/zmk-input-processor-keybind](https://github.com/zettaface/zmk-input-processor-keybind) | 入力プロセッサ keybind |
| [kot149/zmk-mouse-gesture](https://github.com/kot149/zmk-mouse-gesture) `855a6e80...` | マウスジェスチャー（ストロークでキー発火） |
| [cormoran/zmk-module-ble-management](https://github.com/cormoran/zmk-module-ble-management) `851661c` | BLE 管理（v4移行前にpin） |
| [cormoran/zmk-module-battery-history](https://github.com/cormoran/zmk-module-battery-history) | バッテリー履歴 |
| [cormoran/zmk-module-settings-rpc](https://github.com/cormoran/zmk-module-settings-rpc) | Settings RPC |
| [note: razilyis 慣性スクロール記事](https://note.com/razily/n/nea1575614710) | 慣性スクロール実装の参考記事 |
| [keymap-drawer](https://github.com/caksoylar/keymap-drawer) | キーマップ SVG 自動生成ツール |
