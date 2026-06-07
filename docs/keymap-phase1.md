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
- **Backspace** は専用 hold-tap `mt_bspc`（`quick-tap-ms=200`）。タップ→すぐ長押しで **BS をオートリピート**（連続削除）。修飾キー(⌘/Ctrl)の hold はそのまま。他の mod-tap には quick-tap を付けていない。

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
  | `P` | PrintScreen（全画面） | ⌘⇧3（全画面） |
  | `O` | Win+Shift+S（範囲指定） | ⌘⇧4（範囲指定） |
  | `U` | Alt+PrintScreen（アクティブ窓） | `ss_window_mac`＝⌘⇧4→Space（ウィンドウ単位） |
- **Mute** は `H`（右手ホーム内側）に `C_MUTE`（音量±の真上）。両 NAV 共通。
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
- 大西配列・薙刀式（→ 下記「導入案」参照）
- マウスジェスチャー（`zip_mouse_gesture`、外部module追加）→ 下記「マウスジェスチャー実装案」参照
  - **P / Del に tap-mod（tap=通常 / hold=ジェスチャー）で割当予定**。位置は現状の右手側のまま（本人の手に合うとのこと）。
- ホームローMod 本格導入（閾値チューニング込み）
- LANG切替の `eager_tap_dance` 方式（kot版）併存
- Enter長押しの活用 / roBaへの横展開

---

## 大西配列・薙刀式 導入案（実装優先度: 低）

**共通前提**
- OS側配列は引き続き JIS 固定。
- 現状のレイヤー番号 0〜7 は変更しない。追加は 8 番以降。
- BLE層からの切替ボタンとして実装する想定。

### 案 A: `&tog` オーバーレイ方式（大西配列向き・最小コスト）

- 大西配列レイヤー（例: 8）を MAC/WIN の上に重ねる透過レイヤーとして追加。
- 英字キー位置のみ上書き。SYM / NAV / NUM / BLE は `&trans` で素通り。
- BLE層に `&tog 8` ボタン1つで オン/オフ。
- **電源再投入で QWERTY に戻る**か否かは ZMK のフラッシュ保存設定次第（`CONFIG_ZMK_SETTINGS_RESET_ON_START` 等で制御可能）。デフォルトでは `&tog` 状態は保持される点に注意。
- 薙刀式には**不向き**（同時打鍵が単純なレイヤー置換では実現できない）。

### 案 B: `&to` ベース層追加方式（大西・薙刀どちらでも適用可）

- 大西MAC(8) / 大西WIN(9) などの新ベース層を追加。
- BLE層に「大西へ `&to 8`」「QWERTY(Mac)へ戻る `&to MAC`」を追加。
- BTプロファイル連動マクロ（`bt_mac0` 等）も対応する配列を考慮して拡張が必要。
- **電源再投入では戻らない**（`&to` はフラッシュに保存される）ため、BLE層の「QWERTY戻り」ボタンは必須。
- レイヤー数: +2〜4。

### 案 C: `zmk-naginata` モジュール方式（薙刀式の本格対応）

- 外部モジュール（例: `nickcoutsos/zmk-naginata`）を `config/west.yml` に追加。
- 薙刀式の同時打鍵ロジックをモジュールが処理するため、ZMKレイヤーでは実現できない部分を解決できる。
- **要確認**: DYAモジュール（`zmk-module-runtime-input-processor`）との互換性、west.yml の pin 増加。
- 案 B と組み合わせて「薙刀ベース層 + naginata behavior」として実装するイメージ。

### 案 D: OS側IME委託方式（ゼロ実装）

- キーボード側は現状のまま変更なし。OS側のIME（かわせみ3・AquaSKK・ATOK等）に配列変換を任せる。
- ZMK変更ほぼゼロ。手軽だが **OS設定に強依存**。接続先デバイスごとにIME設定が必要。

### 配列別まとめ

| 配列 | 推奨案 | 理由 |
|------|--------|------|
| 大西配列 | **案 A**（手軽）または 案 B | 英字の置換だけで実現可能。`&tog` が最小コスト。 |
| 薙刀式 | **案 C**（本格）または 案 D（手軽妥協） | 同時打鍵は専用モジュールなしでは難しい。 |

---

### 実装前に潰すべき障壁

#### 案 A（大西配列）

**`&tog` は電源を切っても戻らない**
- ZMK はデフォルトで `&tog` 状態をフラッシュに保存する。「電源を切ったら QWERTY に戻る」は標準では動作しない。
- 対策: BLE層に `&to MAC` / `&to WIN` の「QWERTY戻しボタン」を用意する（これが現実的）。`CONFIG_ZMK_SETTINGS_RESET_ON_START` でフラッシュをリセットする方法もあるが副作用が大きい。

**既存コンボが大西配列で暴発する**
- 現状のコンボ（`S`+`D`=Tab / `D`+`F`=Shift+Tab / `J`+`K`=コピー等）は **物理キー番号** で登録されている。
- 大西配列でそれらの位置の文字が変わると、打鍵時にコンボが誤発火する。
- 対策: 大西配列レイヤーの定義時に、競合するコンボを `layers = <MAC WIN>` から外すか、大西配列レイヤー用に別コンボを追加する。実装前にどの物理位置が衝突するか洗い出すこと。

**レイヤー数の上限**
- ZMK のデフォルト上限は16。現状8層なので追加は余裕あり。`mona2_l.conf` / `mona2_r.conf` への `CONFIG_ZMK_KEYMAP_LAYERS_MAX` 追記は不要（上限に近づいたら追加）。

**大西配列のキー定義作業**
- 40〜50キーの置換を `.keymap` に書き起こす純粋な写経作業。誤りを防ぐため、大西配列の公式配列表と照合しながら進めること。

---

#### 案 C（薙刀式 / zmk-naginata）

**ZMK フォーク互換性（最大の障壁）**
- このリポジトリの ZMK 本体は `cormoran/zmk v0.3-branch+dya`（DYA Studio 対応の独自フォーク）。
- `zmk-naginata` は標準 ZMK を前提に開発されており、このフォークで動くかは **事前ビルド検証が必須**。
- 最初の確認手順: `config/west.yml` に naginata モジュールを追加し、keymap への組み込みなしでビルドが通るかだけを確認する。

**モジュールの revision pin**
- `zmk-module-runtime-input-processor` と同様に、naginata モジュールも ZMK v4 移行の影響を受けている可能性がある。
- `west.yml` に追加する際は `revision: main` のまま放置せず、ビルドが通った時点のコミット SHA に pin すること（他モジュールの前例に倣う）。

**薙刀式の定義量**
- 清音・濁音・半濁音・拗音・特殊記号を含めると 300 以上の組み合わせがある。
- モジュールの実装次第でユーザー側の記述量は変わるが、定義ファイルは相応のボリュームになる。実装着手前にモジュールの README と既存ユーザーの `.keymap` 事例を必ず確認すること。

**既存モジュールとの競合リスク**
- `zmk-module-runtime-input-processor`（pin: `dbf92f7`）は入力処理パイプラインを拡張するモジュール。naginata も入力処理に割り込む可能性があり、競合が起きた場合は ZMK 側の割り込み順（`input_processors` の優先度）を調整する必要がある。

---

## マウスジェスチャー実装案（実装優先度: 低）

### モジュール

**`kot149/zmk-mouse-gesture`**（zettaface の `zmk-input-processor-keybind` とは別モジュール）
- `zip_mouse_gesture` という input processor ノードを提供。
- `mona2_r.overlay` の `&trackball_central_listener` の `input-processors` チェーンに追加する。
- 主要パラメータ:
  - `stroke-size = <N>`: ジェスチャー認識に必要な移動距離（デフォルト: 200。PMW3610 CPI=600 環境では 100〜150 程度が目安）
  - `enable-eager-mode`: 方向確定次第即発火（推奨）
  - `gesture-cooldown-ms = <N>`: 連続誤発火防止のクールダウン（例: 200ms）

### ジェスチャーの定義方法

keymap 内で以下のように記述する（`mouse-gesture.dtsi` を include した上で）:

```dts
&zip_mouse_gesture {
    stroke-size = <150>;
    enable-eager-mode;
    gesture-cooldown-ms = <200>;

    back {
        pattern = <GESTURE_LEFT>;
        bindings = <&kp LG(LEFT)>;   // Mac: ⌘← (ブラウザ戻る)
    };
    forward {
        pattern = <GESTURE_RIGHT>;
        bindings = <&kp LG(RIGHT)>;  // Mac: ⌘→ (ブラウザ進む)
    };
    close_tab {
        pattern = <GESTURE_DOWN GESTURE_RIGHT>;  // L字
        bindings = <&kp LG(W)>;
    };
};
```

- 方向は `GESTURE_UP / GESTURE_DOWN / GESTURE_LEFT / GESTURE_RIGHT` の 4 方向。
- 複数方向を並べると L字・Z字等の連続ジェスチャーになる。
- MAC/WIN で修飾キーが異なるため、Phase 1 のコピペコンボ（`layers = <MAC>` / `<WIN>` の 2 本定義）と同じ方式で OS 別に分岐する必要がある。

### 設計方針: GESTURE専用層方式（推奨）

**常時アクティブにしない理由**: `zip_mouse_gesture` をメインの input-processors チェーンに直置きすると、普通のマウス移動でジェスチャーが誤発火する。

**推奨設計**:

1. GESTURE 層（例: 8）を追加。
2. `mona2_r.overlay` の `&trackball_central_listener` に、スクローラー（`scroller {}`）と同様のサブノードを追加し、`layers = <8>` で GESTURE 層のみ有効化。
3. P と Del に `&lt GESTURE P` / `&lt GESTURE DEL`（tap-mod）を割り当て。**hold 中だけ GESTURE 層がアクティブになり、その間のトラックボール操作だけジェスチャーとして処理される。**

```dts
// mona2_r.overlay イメージ
&trackball_central_listener {
    // ...既存の input-processors はそのまま...

    gesturer {
        layers = <8>;   // GESTURE層のみ有効
        input-processors = <&zip_mouse_gesture>;
    };
};
```

```c
// mona2.keymap イメージ（右手 P / Del 位置）
&lt GESTURE P      // tap=P / hold=ジェスチャーモード
&lt GESTURE DEL    // tap=Del / hold=ジェスチャーモード（別アサイン案）
```

**P と Del の役割分け案**（未決定、実装時に検討）:
- P と Del を同一 GESTURE 層につなぐ → どちらを押しても同じジェスチャーセット
- 別々の層（GEST_P / GEST_DEL）にする → 2 倍のジェスチャー数を使い分け可能だがレイヤー数が増える

### west.yml への追加方法

```yaml
- name: zmk-mouse-gesture
  remote: kot149
  revision: main   # 動作確認後に SHA で pin すること
```

リモート定義も追加:
```yaml
- name: kot149
  url-base: https://github.com/kot149
```

### 実装前に潰すべき障壁

**DYAフォーク互換性**
- ZMK 本体が `cormoran/zmk v0.3-branch+dya`。`zmk-mouse-gesture` が標準 ZMK を前提にしていた場合に動作しない可能性がある。
- 確認手順: west.yml に追加して keymap への組み込みなしにビルドだけ通るかを先に確認する（薙刀式・案 C と同様）。

**input-processor チェーンの順序**
- 現状のチェーン: `&zip_xy_transform → &mouse_runtime_input_processor → &zip_temp_layer 6 500`
- `zip_mouse_gesture` は AML 用の `zip_temp_layer` より **後** に置く必要があるか要確認。順序を誤るとジェスチャー認識前に AML が先に処理してしまう。

**stroke-size の実機チューニング**
- PMW3610 の CPI=600 設定に合わせた調整が必要。既存ユーザー事例: 20〜300 と幅が広い。実装後に実機で確認すること。

**レイヤー数**
- GESTURE 層追加で 9 層以上になるが、ZMK のデフォルト上限 16 まで余裕あり。
