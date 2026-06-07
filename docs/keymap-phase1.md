# moNa2 キーマップ — Phase 1 実装まとめ

> このドキュメントは `claude/keymap-rework` ブランチで実装した内容のまとめです。
> **キーマップ図の正**は GitHub Actions(`draw.yml`)が自動生成する [`keymap-drawer/mona2.svg`](../keymap-drawer/mona2.svg)（push毎に更新）。

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
| 0 | WIN | 既定 | QWERTY。修飾キー=Windows系(Ctrl/Win/Alt) |
| 1 | MAC | BTプロファイル連動(BT1) | QWERTY。修飾キー=Mac系(⌘/Ctrl/⌥) |
| 2 | SYM 記号 | Space 長押し | JIS正準の記号一式（`jis.h`経由） |
| 3 | NUM 数字 | 英数(LANG2) 長押し | 右手テンキー（`KP_*`でJIS非依存） |
| 4 | NAV 矢印 | かな(LANG1) 長押し | 左手 逆T字＋Home/End/PgUp/PgDn |
| 5 | MOUSE | オートマウス(AML) ＝ボール操作で自動 | 右手にマウスボタン |
| 6 | BLE/設定 | Escコンボ長押し(英数+かな) | BT/出力/Studio/Boot |

---

## 各レイヤー詳細

### Base (WIN / MAC)
- 英字 QWERTY。両OSで英字・機能層アクセスは共通、**違いは修飾キーのみ**。
  - WIN: `Ctrl / Win(GUI) / Alt`、BS長押し=Ctrl、長音ー長押し=Ctrl
  - MAC: `⌘(GUI) / Ctrl / ⌥(Alt)`、BS長押し=⌘、長音ー長押し=⌘
- `Z` = mod-tap Shift（`&mt LSHFT Z`）
- `L` の右隣 = **長音「ー」**（`JIS_MINUS`、hold=Ctrl/⌘）

### 親指クラスタ
| | 左手 | | | 右手 | |
|---|---|---|---|---|---|
| | BS | Space | 英数(LANG2) | かな(LANG1) | Enter |
| tap | Backspace | Space | 英数(LANG2) | かな(LANG1) | Enter |
| hold | Ctrl/⌘ | **SYM** | **NUM** | **NAV** | — |

### 中央3キー（一等地）
- 左内側 = **Caps Word**（`&caps_word`／1単語だけ大文字）
- 右内側・上 = **`_`**（`JIS_UNDER`／アンダースコア直置き）
- 右内側・中 = **Repeat**（`&key_repeat`／直前キー繰り返し）
- ※ `;` `:` は記号層にあるため基底中央には置かない

### コンボ（sayu-hub 意識）
| コンボ | 動作 |
|---|---|
| `S`+`D` | Tab |
| `D`+`F` | Shift+Tab |
| `英数`+`かな` | tap=Esc / hold=BLE層 |

### SYM（記号）
- `config/jis.h` のエイリアスで JIS-OS でも記号が正しく出る。
- 上段 `! @ # $ %` / `^ & * ( )`、中段 `= + - _ \` / `[ ] { } |`、下段 `` ` ~ : ; ' `` / `" < > ? /`、`¥`。

### NUM（数字・右手テンキー）
```
*  7  8  9  /
+  4  5  6  -
0  1  2  3  .
```
- テンキーHID（`KP_*`）なので配列に依存しない。0 は 1 の左。

### NAV（矢印・左手）
- `E=↑`, `S/D/F=←↓→`（逆T字）, `A=Home`, `G=End`, `Z=PgUp`, `X=PgDn`。

### MOUSE（オートマウスレイヤー）
- 右手に `LCLK / RCLK / MCLK / MB4(戻) / MB5(進)`。
- トラックボール操作で MOUSE 層(=5)へ自動遷移（AML）。

### BLE/設定
- `BT0(Win機) / BT1(Mac機) / BT2(Win機) / BT3 / BT4`、`BTclr / BTclrA`。
- `OUT`(USB/BLE出力切替)、`Studio`(`&studio_unlock`)、`Boot`(`&bootloader`)、F1〜F12。

---

## OS切替（BTプロファイル連動）
- マクロ `bt_win0` / `bt_mac1` / `bt_win2` が「ベース層切替(`&to`)＋`&bt BT_SEL`」をまとめて実行。
  - BT0/BT2 → WIN ベース、BT1 → MAC ベース。
- 接続先デバイス(Win機/Mac機)を選ぶと、対応するベース層へ自動で切り替わる。

## オートマウスレイヤー(AML)
- `boards/shields/mona2/mona2_r.overlay` のトラックボール listener に `&zip_temp_layer 5 500` を配線。
- ボールスクロールのトリガは NAV 層(=4)（= かな長押し中はボールでスクロール）。

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
