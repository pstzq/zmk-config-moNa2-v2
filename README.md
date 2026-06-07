# zmk-config-moNa2-v2

moNa2（右手トラックボール付き分割キーボード）用の ZMK キーマップ設定です。
**JIS運用 / Mac・Windows 切替 / DYA Studio 対応**。

---

<img src="keymap-drawer/mona2_jis.svg">

---

## レイヤー構成

| # | 名称 | 起動方法 |
|---|---|---|
| 0 | **MAC** | デフォルト（電源投入時） |
| 1 | **WIN** | BT プロファイル連動で自動切替 |
| 2 | **SYM** 記号 | `Space` 長押し |
| 3 | **NUM** 数字 | `Enter` 長押し |
| 4 | **NAV-M** 矢印(Mac) | `英数` or `かな` 長押し（MAC ベース時） |
| 5 | **NAV-W** 矢印(Win) | `英数` or `かな` 長押し（WIN ベース時） |
| 6 | **MOUSE** | トラックボール操作で自動遷移（AML） |
| 7 | **BLE/設定** | `英数`+`かな` 同時押し |
| 8 | **GESTURE PAN** | `P` 長押し |
| 9 | **GESTURE SNAP (Mac)** | `Del` 長押し（MAC ベース時） |
| 10 | **GESTURE SNAP (Win)** | `Del` 長押し（WIN ベース時） |

---

## 主な機能

### Mac / Windows 切替

BLE 層（`英数`+`かな` 同時押し）の最上段で切替：

| キー | 動作 |
|---|---|
| Y | BT0 → Mac モード |
| U | BT1 → Windows モード |
| I | BT2 → Windows モード |
| O / P | BT3 / BT4（層は手動切替） |

接続先を選ぶと **ベース層（MAC/WIN）が自動で切り替わり**ます。

---

### ロータリーエンコーダ（左ノブ）

| 使用中のレイヤー | ノブの動作 |
|---|---|
| MAC / WIN / SYM / NUM / MOUSE / GESTURE | スクロール（上下） |
| **NAV-M / NAV-W / BLE** | **音量調整** |

---

### トラックボール

| 状態 | 動作 |
|---|---|
| 通常 | マウスカーソル移動 |
| NUM / NAV / BLE 層中 | スクロール（慣性スクロール対応） |
| `P` 長押し中 | **パン**（2D 自由スクロール） |
| `Del` 長押し中（Mac） | **ウィンドウスナップ**（Rectangle） |
| `Del` 長押し中（Win） | **ウィンドウスナップ**（Win+矢印） |

トラックボールを動かすと **MOUSE 層へ自動遷移**（AML）、500ms 静止で元に戻ります。

#### ウィンドウスナップ ジェスチャー

`Del` を押したままトラックボールを弾く方向でスナップ先が変わります：

| ストローク方向 | Mac（Rectangle） | Windows |
|---|---|---|
| ← | 左半分 | 左半分 |
| → | 右半分 | 右半分 |
| ↑ | 最大化 | 最大化 |
| ↓ | 中央（1/2） | 元のサイズに戻す |

> Mac は [Rectangle](https://rectangleapp.com/) が必要です（デフォルトショートカット `Ctrl+Option+矢印`）。

---

### コンボ

| 同時押し | 動作 |
|---|---|
| `S` + `D` | Tab |
| `D` + `F` | Shift + Tab |
| `J` + `K` | コピー（Mac: ⌘C / Win: Ctrl+C） |
| `K` + `L` | ペースト（Mac: ⌘V / Win: Ctrl+V） |
| `英数` + `かな` | tap = Esc / hold = BLE 層 |

---

### NAV 層（矢印・右手）

```
ESC  —   ↑   —   [Mission Control/タスクビュー]    —  [スクショW]  ↑  [スクショ範囲]  [スクショ全画面]
Home ←   ↓   →  End                           Mute  ←   ↓   →    —
Shift PgUp PgDn  —   —                              🔅  ⏮   ⏯   ⏭  🔆
```

左手は逆T字配列、右手は IJKL 逆T字＋メディアキー。

---

## 書き込み方法

1. このリポジトリへ push すると GitHub Actions が自動でファームウェアをビルド
2. Actions の完了後、実行ページ下部の **Artifacts > firmware** をダウンロード
3. `mona2_l-seeeduino_xiao_ble.uf2` → 左手、`mona2_r-seeeduino_xiao_ble.uf2` → 右手
4. **初回またはキーマップ構造を大きく変更した場合は `settings_reset.uf2` も先に書き込む**

---

## DYA Studio でのキーマップ変更

[DYA Studio](https://studio.dya.cormoran.works/) を使うと GUI でキーマップを変更できます。
接続前に BLE 層の `studio_unlock` キーを押してください（`L` の右隣）。

詳細: [`README2.md`](README2.md)

---

## COROPIT をお使いの方

`mona2_r.overlay` の以下の行のコメントアウトを外してください：

```dts
invert-x;
invert-y;
```

---

## 設計ドキュメント

詳細な設計思想・実装経緯・今後の拡張案: [`docs/keymap-phase1.md`](docs/keymap-phase1.md)
