# HHKB Hybrid HID プロトコル仕様

ソース: [happy-hacking-gnu](https://gitlab.com/dom/happy-hacking-gnu) の逆解析結果

## デバイス識別

| 項目 | 値 |
|-----|-----|
| Vendor ID | `0x04fe` |
| Product ID | `0x0020` / `0x0021` / `0x0022` |
| 対象インターフェース | Interface #2（ベンダー固有） |
| macOS での識別 | usage_page `0xFF00` |

## パケット構造（65 バイト）

```
Offset  Size  内容
------  ----  ----
0       1     Report ID (常に 0x00)
1       1     Magic (0xAA)
2       1     Magic (0xAA)
3       1     コマンド ID
4-64    61    ペイロード（コマンドによって異なる）
```

## コマンド一覧

| 名前 | ID (dec) | ID (hex) | 説明 |
|------|----------|----------|------|
| NOTIFY_APPLICATION_STATE | 1 | 0x01 | アプリ状態通知 |
| GET_KEYBOARD_INFO | 2 | 0x02 | キーボード情報取得 |
| RESET_FACTORY_DEFAULTS | 3 | 0x03 | 工場出荷状態リセット |
| CONFIRM_KEYMAP | 4 | 0x04 | キーマップ確認 |
| GET_DIP_STATE | 5 | 0x05 | DIP スイッチ状態取得 |
| GET_KEYBOARD_MODE | 6 | 0x06 | キーボードモード取得 |
| RESET_DIPSW | 7 | 0x07 | DIP リセット |
| **WRITE_KEYMAP** | **134** | **0x86** | **キーマップ書き込み** |
| **GET_KEYMAP** | **135** | **0x87** | **キーマップ読み取り** |
| **DUMP_FIRMWARE** | **208** | **0xD0** | **ファームウェアダンプ** |
| FIRMUP_MODE_CHANGE | 224 | 0xE0 | ファームウェア更新モード移行 |
| **FIRMUP_START** | **225** | **0xE1** | **ファームウェア更新開始** |
| **FIRMUP_SEND** | **226** | **0xE2** | **ファームウェアデータ送信** |
| **FIRMUP_END** | **227** | **0xE3** | **ファームウェア更新終了** |
| UPDATEBOOT_* | 228-231 | 0xE4-0xE7 | ⚠️ ブートローダ更新（bricking リスク） |

## GET_KEYBOARD_INFO (0x02)

### レスポンス

```
Offset  内容
------  ----
4       type_number
5       revision
6-17    serial (ASCII, null-terminated)
18-20   app firmware version (major.minor.patch)
21-23   boot firmware version
24      running firmware (0=app, 1=bootloader)
```

## GET_KEYMAP (0x87) / WRITE_KEYMAP (0x86)

### 構造

128 キー分のデータを 3 回のやり取りで送受信する。

**GET_KEYMAP 受信（3 回）:**

| 回 | データ量 | データ開始オフセット |
|----|---------|-----------------|
| 1 | 58 bytes | +6 |
| 2 | 58 bytes | +6 |
| 3 | 12 bytes | +6 |
| 合計 | **128 bytes** | |

**WRITE_KEYMAP 送信（3 回）:**

| 回 | buf[4] | 送信データ量 |
|----|--------|------------|
| 1 | 0x41   | 57 bytes |
| 2 | 0x82   | 59 bytes |
| 3 | 0xC3   | 12 bytes |

### キーコードフォーマット

128 バイトのうち各バイトが 1 キーに対応（HID usage code）。
レイヤー構成は Base / Fn1 の 2 レイヤー（各 60 キー + メタデータ 8 バイト相当）。

> **重要:** この範囲で設定できるのは「どのキーをどのキーコードに変える」という 1:1 マッピングのみ。  
> mod-tap のような「タイミング依存の動作」はキーマップデータには含まれず、**ファームウェア本体に実装する必要がある。**

## DUMP_FIRMWARE (0xD0)

> ## 🛑🛑 実機検証結果（JIS / PD-KB820B, 2026-06-13）：`0xD0` は安全なダンプではない
>
> JIS 機（PID=0x0022, PD-KB820BS）で `0xD0` を送ったところ、**読み取り専用ダンプにはならず、
> ファームウェア更新モードへ移行した**。
> - キーボードが Enter 連打のようなゴミ HID レポートを出力
> - 直後の `info` で `running: bootloader`, `app_firmware: 255.255.255`(=0xFF, 消去済みに見える) を返した
> - **書き込みを一切しなかったため、タイムアウト／再列挙で無傷のアプリに自己復帰**（`running: app` に戻り打鍵も正常化）
>
> **結論：ANSI 由来の「0xD0 = 安全な読み取りダンプ」という前提は JIS では成立しない。
> このコマンドは更新モード移行を誘発する危険コマンドとして扱うこと。安易に送らない。**
> 復旧は「何も書かない（特に FIRMUP_*/UPDATEBOOT_* を送らない）」ことで成立した。

### 手順（※上記の通り JIS では想定どおり動かない。ANSI 向けの記録として残す）

1. コマンド送信（ペイロードなし）
2. レスポンスを繰り返し受信
   - 各パケットのデータは **オフセット +8 から 56 バイト**
   - 56 バイト未満のパケットが来たら終了
3. 合計 ~300 KB

### ファームウェア構造（既知部分）

```c
typedef struct {
    char     crc16[2];      // 先頭 2 バイト: CRC16 チェックサム
    uint8_t *raw_data;      // 実データへのポインタ
    int      file_size;
} hhkb_firmware;
```

**⚠️ 暗号署名の痕跡なし。CRC16 のみで整合性チェックされている可能性が高い。**

## FIRMUP シーケンス (0xE1 → 0xE2 × N → 0xE3)

### FIRMUP_START (0xE1)

```
Offset  内容
------  ----
0       0x00 (report ID)
1-2     0xAA 0xAA (magic)
3       0xE1 (command)
4       0x00
5       0x08
6-9     firmware file_size (4 bytes, little-endian)
10-11   CRC16 (2 bytes, from firmware file先頭)
```

### FIRMUP_SEND (0xE2)

```
Offset  内容
------  ----
3       0xE2
5       packet_length + 2
6-7     packet_num (2 bytes, little-endian)
8+      firmware data (最大 57 bytes/パケット)
```

パケット数計算: `ceil((file_size - 2) / 57)`  
（先頭 2 バイトの CRC16 は送信しない）

### FIRMUP_END (0xE3)

コマンドのみ（ペイロードなし）

## 参考リンク

- [happy-hacking-gnu (GitLab)](https://gitlab.com/dom/happy-hacking-gnu) — HID プロトコル実装
- [hhkb-studio-tools (GitHub)](https://github.com/yuja/hhkb-studio-tools) — HHKB Studio 用（類似プロトコル）
