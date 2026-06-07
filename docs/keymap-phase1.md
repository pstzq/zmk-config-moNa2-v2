# moNa2 キーマップ — Phase 1 実装まとめ

> このドキュメントは `claude/keymap-rework` ブランチで実装した内容のまとめです。
> **キーマップ図**は GitHub Actions(`draw.yml`)が push 毎に自動生成（2種類）：
> - US(ANSI)準拠: [`keymap-drawer/mona2.svg`](../keymap-drawer/mona2.svg)（keymap-drawer標準。記号は `Sft+1` `[` 等のUS表記）
> - **JIS準拠**: [`keymap-drawer/mona2_jis.svg`](../keymap-drawer/mona2_jis.svg)（`scripts/jis_relabel.py` で JIS で実際に出る記号 `@ : ^ ¥` 等に変換した版）

## 目的
- 日本語(JIS)環境での **US/JIS 記号の読み替えの煩雑さ** を恒久的に解消する。
- Mac / Windows 併用での差分を整理する。

## 前提
- OS側キーボード配列は **Mac・Windows とも JIS** で統一運用。
- Mac=標準IME / Windows=Google日本語入力。
- **DYA Studio**(ZMK Studio系GUI)対応。
- 対象: moNa2（右手トラックボール）。

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
| 4 | NAV-M 矢印(Mac) | 英数 or かな 長押し ※MACベース時 | 左手 逆T字＋Home/End/PgUp/PgDn。右手矢印IJKL/メディア |
| 5 | NAV-W 矢印(Win) | 英数 or かな 長押し ※WINベース時 | 左手 逆T字＋Home/End/PgUp/PgDn。右手矢印IJKL/メディア |
| 6 | MOUSE | オートマウス(AML) ＝ボール操作で自動 | 右手にマウスボタン |
| 7 | BLE/設定 | 英数 ＆ かな 同時押し(コンボ) | Bluetooth/出力/Studio/Boot のみ |

---

## 各レイヤー詳細

### Base (WIN / MAC)
- 英字 QWERTY。両OSで英字・機能層アクセスは共通、**違いは修飾キーのみ**。
  - MAC: `⌘(GUI) / Ctrl / ⌥(Alt)`、BS長押し=⌘、長音ー長押し=⌘
  - WIN: `Ctrl / Win(GUI) / Alt`、BS長押し=Ctrl、長音ー長押し=Ctrl
- `Z` = mod-tap Shift（`&mt LSHFT Z`）
- `L` の右隣 = **長音「ー」**（`JIS_MINUS`、hold=Ctrl/⌘）

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

### SYM（記号）
- `config/jis.h` のエイリアスで JIS-OS でも記号が正しく出る。
```
上段:  !  "  #  $  %        &  '  (  )  |
中段:  ^  ~  +  -  *    `   {  }  [  ]    =
下段:  1  2  3  4  5   ; :  6  7  8  9    0      (最下段に ¥)
```
- 上段: 数字段の Shift 面 `! " # $ %` / `& ' ( ) |`。`|` は P 位置に1つ。
- 中段（ホーム行）: 左 `^ ~ + - *` / 中央 `` ` `` / 右 `{ } [ ]` ＋ `=`（ー位置）。演算子・括弧を集約。
- 下段: 数字 `1〜5` / 中央 `; :`（左がセミコロン）/ `6〜0`。SYM 内で数字直打ちが可能。
- `< > ?` は SYM に持たず、ベース層の `, . /` ＋ Shift で出す割り切り。
- `\`（バックスラッシュ）は **JIS では入力にクセがあり、`¥`（最下段 `JIS_YEN`）がその役割を兼ねる**ため SYM には置かない（意図的。戻さないこと）。`_` はベース層中央に常設。

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
  | `P` | PrintScreen | ⌘⇧3（スクリーンショット） |
- 右手下段メディアキー（両 NAV 共通）: `M / , / .` ＝ `⏮ ⏯ ⏭`（`C_PREV / C_PP / C_NEXT`）、両端 `N / /` ＝ `🔉 🔊`（`C_VOL_DN / C_VOL_UP`）。

### MOUSE（オートマウスレイヤー）
- 右手に `LCLK / RCLK / MCLK / MB4(戻) / MB5(進)`。
- トラックボール操作で MOUSE 層(=6)へ自動遷移（AML）。

### BLE/設定（Bluetooth・端末管理に限定）
- **雑多なキーは置かず Bluetooth まわりに集中**：`BT0=Mac / BT1=Win / BT2=Win / BT3 / BT4`、`BTclr / BTclrA`。
- 端末管理: `OUT`(USB/BLE出力切替)、`Studio`(`&studio_unlock`)、`Boot`(`&bootloader`)。
- F1〜F12 は **NUM 層左手**へ、メディアキーは **NAV 層右手**へ移設済み。
- エンコーダは `rsr_vol`（ボリューム）に切り替わる。

---

## OS切替（BTプロファイル連動）
- マクロ `bt_mac0` / `bt_win1` / `bt_win2` が「ベース層切替(`&to`)＋`&bt BT_SEL`」をまとめて実行。
  - BT0 → MAC ベース、BT1/BT2 → WIN ベース。
- デフォルト(電源投入時)は MAC ベース（layer 0）。
- 接続先デバイス(Mac機/Win機)を選ぶと、対応するベース層へ自動で切り替わる。

## オートマウスレイヤー(AML)
- `boards/shields/mona2/mona2_r.overlay` のトラックボール listener に `&zip_temp_layer 6 500` を配線。
- ボール操作で MOUSE 層(=6) へ自動遷移、500ms 操作なしで復帰。
- ボールスクロールのトリガは NUM(=3) / NAV_MAC(=4) / NAV_WIN(=5)（`layers = <3 4 5>`）。LANG2(NUM) 長押し中にもスクロール可能。

## 依存モジュールのpin（重要）
DYAモジュールの `revision: main` が浮動で、`zmk-module-runtime-input-processor` が **2026-04-30 に zmk v4 へ移行** → fork(`v0.3-branch+dya`)と非互換になりビルド失敗(`too many arguments to zmk_keymap_layer_activate`)。shakupan版に倣い `config/west.yml` で v4移行前にpin：
- `zmk-module-runtime-input-processor`: `main` → `dbf92f7`
- `zmk-module-ble-management`: `main` → `851661c`

---

## ビルド & 書き込み
- push すると GitHub Actions(`build.yml`)が uf2 を生成。実行ページ下部の Artifacts `firmware` をDL。
- 含まれる uf2: `mona2_l` / `mona2_r` / `settings_reset`。
- **キーマップ構造が大きく変わったため、初回は `settings_reset` も一度書き込む**ことを推奨（旧設定の残留防止）。

## 実機で要確認
- AML（ボール操作でMOUSE層へ）。
- JIS記号が各キーで意図通り出るか（OS側JIS設定）。
- OS切替（BLE層 BT0/BT1/BT2）でWIN/MACベースが切り替わるか。

## Phase 2（今後）
- 大西配列（裏の裏トグル）
- マウスジェスチャー（`zip_mouse_gesture`、外部module追加）
- ホームローMod 本格導入（閾値チューニング込み）
- LANG切替の `eager_tap_dance` 方式（kot版）併存
- Enter長押しの活用 / roBaへの横展開
