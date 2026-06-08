# 次のステップ詳細

## Phase 1：ファームウェアダンプ（MacBook で実施）

### 準備

```bash
# Python hid ライブラリ（HIDAPI の Python バインディング）
pip3 install hid

# binwalk（アーキテクチャ解析）
brew install binwalk
```

### 実行

```bash
# 接続確認（インターフェース一覧）
sudo python3 scripts/hhkb_hid.py list

# キーボード情報（シリアル、ファームバージョン確認）
sudo python3 scripts/hhkb_hid.py info

# ファームウェアダンプ
sudo python3 scripts/hhkb_hid.py dump-firmware firmware.bin
```

### トラブルシューティング

**`usage_page=0xFF00` が見つからない場合:**
- `list` コマンドで全インターフェースを確認
- `find_programming_interface()` の USAGE_PAGE 定数を実際の値に変更する
- macOS のシステム環境設定でアクセシビリティ権限を確認

**Permission denied:**
- `sudo` を付けて実行
- または `/etc/sudoers` で Python に権限を付与

---

## Phase 2：アーキテクチャ特定

```bash
# CPU アーキテクチャの推定
binwalk -A firmware.bin

# 文字列から手がかりを探す
strings firmware.bin | grep -iE 'version|copyright|renesas|nordic|arm|cortex'

# エントロピー解析（暗号化・圧縮の有無を確認）
binwalk -E firmware.bin
```

### 期待される結果

- **ARM Thumb2** → Renesas RX/RA、STM32、nRF52 系のいずれか
- エントロピーが均一に高い → 暗号化されている可能性（残念ながら詰み）
- エントロピーが低い部分がある → 解析可能

---

## Phase 3：Ghidra での逆アセンブル

### セットアップ

1. [Ghidra](https://ghidra-sre.org/) をダウンロード・インストール
2. 新規プロジェクト作成
3. `firmware.bin` をインポート
   - Language: binwalk で判明したアーキテクチャを選択
   - Base address: `0x00000000`（不明な場合のデフォルト）
4. Auto-analyze を実行

### 探すべきもの

```
1. キー入力ループ
   - "scan matrix" 相当の処理
   - タイマー割り込みハンドラ
   - HID レポート生成コード

2. キーコードテーブル
   - ROM 上に並んだバイト配列（HID usage codes）
   - GET_KEYMAP の返値と一致するはず

3. mod-tap を追加できそうな場所
   - キーダウン/キーアップのイベント処理
   - タイマー参照が近くにあれば ◎
```

---

## Phase 4：ファームウェア改変（最難関）

### CRC16 の計算

```python
import struct

def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
        crc &= 0xFFFF
    return crc

# 改変後のファームウェアに CRC16 を付け直す
with open('firmware_modified.bin', 'rb') as f:
    body = f.read()[2:]   # 先頭 2 バイト (CRC) を除く

crc = crc16_ccitt(body)
new_fw = struct.pack('<H', crc) + body

with open('firmware_patched.bin', 'wb') as f:
    f.write(new_fw)
```

### 書き戻し

`scripts/hhkb_hid.py` にまだ実装していないが、プロトコルは [docs/protocol.md](./protocol.md) に記載済み。
`FIRMUP_START → FIRMUP_SEND × N → FIRMUP_END` のシーケンス。

> **ここまで来たら先に必ずバックアップのファームウェアを保存しておくこと。**

---

## リスク評価

| リスク | 内容 | 対策 |
|-------|------|------|
| 文鎮化 | 書き込み中断など | ファームウェアダンプをバックアップ保存してから臨む |
| CRC 検証失敗 | キーボード側がリジェクト | 何も変わらないだけ（文鎮化しない） |
| 署名検証の存在 | 実は署名があった | ダンプした時点でわかる（逆アセンブルで確認） |
| ブートローダ破壊 | `UPDATEBOOT_*` 誤使用 | このコマンドには絶対触らない |
