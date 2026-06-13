# JIS 配列固有の調査事項

`happy-hacking-gnu` は ANSI 配列向けに開発されている。  
JIS 配列（HHKB Professional Hybrid Type-S JIS）では以下を独自に確認する必要がある。

## 1. Product ID の確認

まず `list` コマンドで実際の PID を確認する。

```bash
sudo python3 scripts/hhkb_hid.py list
```

期待される出力例:
```
[0] PID=0x0022  usage_page=0xff00  usage=0x0001  path=...
[1] PID=0x0022  usage_page=0x0001  usage=0x0006  path=...
[2] PID=0x0022  usage_page=0x000c  usage=0x0001  path=...
```

→ **PID をメモして `scripts/hhkb_hid.py` の `PRODUCT_IDS` リストに追加する**

## 2. キー数の違い

| モデル | キー数 | 追加キー |
|-------|-------|---------|
| ANSI US | 60 | — |
| JIS | 65〜68 | 変換、無変換、ろ、半角/全角、￥ など |

JIS HHKB のキー配列（参考）:
```
半角  1   2   3   4   5   6   7   8   9   0   -   ^   ¥  BS
Tab   Q   W   E   R   T   Y   U   I   O   P   @   [      Del
Ctrl  A   S   D   F   G   H   J   K   L   ;   :   ]  Ret
Shift     Z   X   C   V   B   N   M   ,   .   /   \  Shift
      Fn  ◆  無変換      Space       変換   カナ  Fn
```

## 3. GET_KEYMAP のサイズ確認

ANSI では 128 bytes（3パス: 58+58+12）だが、JIS では異なる可能性がある。

### 確認手順

スクリプトを **raw モード**（サイズ指定なし）で動かして実際に何バイト来るかを見る。

```python
# 一時的な確認コード（scripts/hhkb_hid.py の get_keymap を置き換えて実行）
def probe_keymap(dev):
    dev.write(make_packet(CMD_GET_KEYMAP))
    time.sleep(0.05)
    
    all_data = []
    for i in range(5):   # 最大 5 パスまで受信してみる
        resp = dev.read(64, timeout_ms=500)
        if not resp:
            print(f"Pass {i+1}: timeout (= no more data)")
            break
        print(f"Pass {i+1}: {bytes(resp).hex()}")
        all_data.extend(resp)
    
    print(f"Total bytes received: {len(all_data)}")
```

### 結果の読み方

- 3パスで終わるなら ANSI と同じ構造（バイト数だけ違う可能性）
- パス数が多い → JIS 用の異なるプロトコルあり
- 各パスの `buf[4]` が `0x41, 0x82, 0xC3` 以外の値 → オフセットが異なる

## 4. ファームウェアダンプ（JIS でも同じはず）

ダンプはキー配列に依存しない処理なので、ANSI と同じコマンド `0xD0` で動くはず。

```bash
sudo python3 scripts/hhkb_hid.py dump-firmware firmware_jis.bin
```

成功したらファイルサイズを確認:
```bash
ls -lh firmware_jis.bin
# 約 300KB なら正常
```

→ サイズが著しく異なる場合は JIS 専用のロジックがある可能性

## 5. 調査結果の記録フォーマット

実行後、以下の情報をこのファイルに追記してください。

```
## 実測値（記録日: YYYY-MM-DD）

- Product ID: 0x????
- usage_page（プログラミング IF）: 0x????
- GET_KEYMAP パス数: ?
- GET_KEYMAP 総バイト数: ? bytes
- firmware.bin サイズ: ? bytes
- binwalk -A の出力（アーキテクチャ）:
```

## 実測値（記録日: 2026-06-13 / Windows / PD-KB820B）

- モデル: HHKB Professional HYBRID Type-S 日本語配列（`serial`=`PD-KB820BS`）
- **Product ID: `0x0022`（JIS 確定）**
- **プログラミング IF: あり**（`list` の [5]: `MI_02`, `usage_page=0xff00`, `usage=0x0001`）
- GET_INFO (0x02): **応答あり**。ただし JIS ではオフセットが ANSI と異なる
  - `serial`(offset 6-17) は正しく `PD-KB820BS` を返す
  - `app_firmware`/`boot_firmware`(offset 18-23) は正常時でも `0.0.0` → **ANSI 用パーサのオフセット誤り。実バージョンは別位置**
- **DUMP_FIRMWARE (0xD0): 🛑 危険。ダンプにならず更新モード移行を誘発**
  - Enter 連打のゴミ HID 出力 → `running: bootloader`, fw=`255.255.255`(=0xFF)
  - **書き込みを一切しなかったため自己復帰**（`running: app` に回復、打鍵正常化）
  - GET_KEYMAP/probe-keymap, firmware.bin サイズ: **未取得（0xD0 が危険と判明したため中断）**

### 次にやるなら（安全側の再検討が必要）
- `0xD0` 経由のダンプ路線は JIS では危険。安全な吸い出し経路が別にあるか、
  あるいは **ソフト側 mod-tap（Karabiner/Kanata）やコントローラ換装（ZMK）** に切り替えるか要判断。

## 6. JIS 先行事例の調査

ANSI の happy-hacking-gnu 相当の JIS 版が存在するかを確認する。

```bash
# 調査用キーワード
# "HHKB" "JIS" "HID" "keymap" "firmware" site:github.com
# "HHKB" "日本語配列" "HID" "ファームウェア"
```

もし JIS 版の解析済みツールが見つかれば、キーマップ構造を流用できる。
