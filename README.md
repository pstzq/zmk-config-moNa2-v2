# HHKB Professional Hybrid Type-S (JIS) — Firmware Research

HHKB Hybrid Type-S **JIS 配列**に mod-tap を入れることを目的とした調査ノート。

## ⚠️ JIS 配列固有の注意点

調査のベースにした `happy-hacking-gnu` は **ANSI 配列専用**として書かれている。  
JIS 配列では以下が未検証であり、独自調査が必要な可能性がある。

| 項目 | ANSI（解析済み） | JIS（要確認） |
|------|----------------|--------------|
| Product ID | 0x0020〜0x0021 | **0x0022 の可能性あり（要 `list` で確認）** |
| キー総数 | 60 キー | **65〜68 キー（変換・無変換・ろ など追加）** |
| GET_KEYMAP サイズ | 128 bytes (3パス) | **異なる可能性あり（要実測）** |
| DUMP_FIRMWARE | 動作確認済み | **同じ経路のはず（最初に確認すべき）** |

→ 詳細は [docs/jis.md](./docs/jis.md) を参照。

## TL;DR（現時点の結論）

- PFU 公式の Keymap Tool は USB HID プロトコルで動いており、**プロトコルは完全に解析済み（ANSI）**
- ファームウェアは HID 経由で **丸ごとダンプ可能**（コマンド `0xD0`）
- 保護は **CRC16 のみ**。暗号署名は確認されていない
- つまり「ダンプ → 改変 → CRC16 再計算 → 再書き込み」の経路が存在する可能性がある
- ただし MCU アーキテクチャの特定と逆アセンブルが必要（未完了）

## ステップ別進捗

| ステップ | 状態 | メモ |
|---------|------|------|
| HID プロトコル解析（ANSI） | ✅ 完了 | [docs/protocol.md](./docs/protocol.md) |
| JIS 固有仕様の確認 | ⏳ 要実行 | [docs/jis.md](./docs/jis.md) に手順あり |
| macOS 用通信スクリプト | ✅ 作成済み | [scripts/hhkb_hid.py](./scripts/hhkb_hid.py) |
| ファームウェアダンプ | ⏳ 要実行 | まずここから（JIS でも同じはず） |
| MCU 特定（binwalk） | ⏳ 要実行 | ダンプ後に実施 |
| 逆アセンブル（Ghidra） | ⏳ 未着手 | MCU 判明後 |
| mod-tap ロジック移植 | ⏳ 未着手 | キー処理ループを特定してから |

## 次にやること（MacBook で）

```bash
# 1. 依存ライブラリをインストール
pip3 install hid

# 2. キーボードを USB 接続して情報を確認
sudo python3 scripts/hhkb_hid.py info

# 3. ファームウェアをダンプ
sudo python3 scripts/hhkb_hid.py dump-firmware firmware.bin

# 4. アーキテクチャを特定
brew install binwalk
binwalk -A firmware.bin
strings firmware.bin | head -60
```

その後、ダンプした `firmware.bin` を Ghidra で読み込む。

## 注意

- ファームウェア書き換えはキーボードが文鎮化するリスクがある
- `UPDATEBOOT_*` コマンドは**絶対に使わない**（ブートローダ更新、bricking リスクあり）
- アプリケーションファームウェア（`FIRMUP_*`）のみ対象にする
