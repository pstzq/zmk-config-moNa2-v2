# HHKB Professional Hybrid / Type-S — Firmware Research

HHKB Hybrid Type-S に mod-tap を入れることを目的とした調査ノート。

## TL;DR（現時点の結論）

- PFU 公式の Keymap Tool は USB HID プロトコルで動いており、**プロトコルは完全に解析済み**
- ファームウェアは HID 経由で **丸ごとダンプ可能**（コマンド `0xD0`）
- 保護は **CRC16 のみ**。暗号署名は確認されていない
- つまり「ダンプ → 改変 → CRC16 再計算 → 再書き込み」の経路が存在する可能性がある
- ただし MCU アーキテクチャの特定と逆アセンブルが必要（未完了）

## ステップ別進捗

| ステップ | 状態 | メモ |
|---------|------|------|
| HID プロトコル解析 | ✅ 完了 | [protocol.md](./docs/protocol.md) |
| macOS 用通信スクリプト | ✅ 作成済み | [hhkb_hid.py](./scripts/hhkb_hid.py) |
| ファームウェアダンプ | ⏳ 要実行 | スクリプトで取得する |
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
