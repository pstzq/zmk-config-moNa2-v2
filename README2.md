# compatible_DYAStudio メモ

`moNa2` で [DYA Studio](https://studio.dya.cormoran.works/) 関連機能を使うための設定メモです。

DYA Studioに接続するときは、事前に「`&studio_unlock`」をキーマップに仕込んでおきます。  
こちらを押した状態でないとDYA Studioへの接続ができません。  
（前提: `CONFIG_ZMK_STUDIO_LOCKING=y`）

## 参照モジュール

- [DYA Studio](https://studio.dya.cormoran.works/)
- [runtime-input-processor](https://github.com/cormoran/zmk-module-runtime-input-processor)
- [runtime-sensor-rotate](https://github.com/cormoran/zmk-behavior-runtime-sensor-rotate)
- [battery-history](https://github.com/cormoran/zmk-module-battery-history)
- [ble-management](https://github.com/cormoran/zmk-module-ble-management)
- [settings-rpc](https://github.com/cormoran/zmk-module-settings-rpc)

## 1. `config/west.yml` 例

> ⚠️ **権威ある定義は [`config/west.yml`](config/west.yml) が常に正**です。以下は DYA 関連の最小構成を示す抜粋で、
> 実際のリビジョンは v4 移行回避のため一部 SHA で pin しています（`revision: main` のままコピーすると
> `too many arguments to zmk_keymap_layer_activate` 等のビルド失敗を踏みます）。慣性スクロール・マウスジェスチャーの
> モジュールも実 config には含まれます。詳細は config/west.yml と docs/keymap-phase1.md の「依存モジュールのpin」を参照。

```yaml
manifest:
  remotes:
    - name: cormoran
      url-base: https://github.com/cormoran
    - name: razilyis    # <-- PMW3610 慣性スクロール対応フォーク
      url-base: https://github.com/razilyis
    - name: kot149      # <-- Mouse Gesture
      url-base: https://github.com/kot149

  projects:
    - name: zmk
      remote: cormoran
      revision: v0.3-branch+dya
      import: app/west.yml

    - name: zmk-module-ble-management
      remote: cormoran
      revision: 851661c   # v4移行前にpin

    - name: zmk-module-battery-history
      remote: cormoran
      revision: main

    - name: zmk-module-settings-rpc
      remote: cormoran
      revision: main

    - name: zmk-module-runtime-input-processor
      remote: cormoran
      revision: dbf92f7   # v4移行前にpin

    - name: zmk-behavior-runtime-sensor-rotate
      remote: cormoran
      revision: main

    - name: zmk-pmw3610-driver
      remote: razilyis
      revision: Dev-v0.3_inertial-scroll

    - name: zmk-mouse-gesture
      remote: kot149
      revision: 855a6e80f18f4b19ea2181648ac062ec72876ece

  self:
    path: config
```

## 2. `mona2_r.conf`（Central 側）

```conf
# ZMK Studio
CONFIG_ZMK_STUDIO=y
CONFIG_ZMK_STUDIO_LOCKING=y

# zmk-module-ble-management
CONFIG_ZMK_BLE_MANAGEMENT=y
CONFIG_ZMK_BLE_MANAGEMENT_STUDIO_RPC=y

# zmk-module-battery-history
CONFIG_ZMK_BATTERY_HISTORY=y
CONFIG_ZMK_BATTERY_HISTORY_STUDIO_RPC=y
CONFIG_ZMK_BATTERY_SKIP_IF_USB_POWERED=n

# zmk-module-settings-rpc
CONFIG_ZMK_SETTINGS_RPC=y
CONFIG_ZMK_SETTINGS_RPC_STUDIO=y

# Split relay / central stack
CONFIG_ZMK_SPLIT_RELAY_EVENT=y
CONFIG_ZMK_SPLIT_BLE_CENTRAL_SPLIT_RUN_STACK_SIZE=3096

# zmk-module-runtime-input-processor
CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR=y
CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR_STUDIO_RPC=y

# zmk-behavior-runtime-sensor-rotate
CONFIG_ZMK_RUNTIME_SENSOR_ROTATE=y
CONFIG_ZMK_RUNTIME_SENSOR_ROTATE_STUDIO_RPC=y

# settings persistence
CONFIG_SETTINGS=y
CONFIG_ZMK_SETTINGS_SAVE_DEBOUNCE=10000
```

## 3. `mona2_l.conf`（Peripheral 側）

```conf
# zmk-module-battery-history
CONFIG_ZMK_BATTERY_HISTORY=y

# zmk-module-settings-rpc
CONFIG_ZMK_SETTINGS_RPC=y

# Split relay / settings persistence
CONFIG_ZMK_SPLIT_RELAY_EVENT=y
CONFIG_SETTINGS=y
CONFIG_ZMK_SETTINGS_SAVE_DEBOUNCE=10000
```

注記:
- `CONFIG_ZMK_RUNTIME_SENSOR_ROTATE=y` は Central 側（`mona2_r.conf`）のみ有効化する。

## 4. CI workflow

`.github/workflows/build.yml` の reusable workflow は DYA 対応forkを使う。

```yaml
jobs:
  build:
    uses: cormoran/zmk/.github/workflows/build-user-config.yml@v0.3-branch+dya
```

## 5. `.keymap` の include

```dts
#include <input/processors.dtsi>
#include <input/processors/runtime-input-processor.dtsi>
#include <behaviors/runtime-sensor-rotate.dtsi>
#include <behaviors/battery_history_request.dtsi>
```

## 6. `.keymap` の runtime-sensor-rotate 例

```dts
behaviors {
    rsr_vol: rsr_vol {
        compatible = "zmk,behavior-runtime-sensor-rotate";
        #sensor-binding-cells = <0>;
        tap-ms = <20>;
        cw-binding = <&kp C_VOL_DN>;
        ccw-binding = <&kp C_VOL_UP>;
    };

    rsr_pg: rsr_pg {
        compatible = "zmk,behavior-runtime-sensor-rotate";
        #sensor-binding-cells = <0>;
        tap-ms = <20>;
        cw-binding = <&kp PG_UP>;
        ccw-binding = <&kp PAGE_DOWN>;
    };
};
```

```dts
sensor-bindings = <&rsr_vol>;
sensor-bindings = <&rsr_pg>;
```

## 7. `mona2_r.overlay` の runtime-input-processor 設定

`CONFIG_ZMK_RUNTIME_INPUT_PROCESSOR=y` だけでは不十分で、`input-listener` 側にも runtime processor の指定が必要。

```dts
#include <input/processors.dtsi>
#include <input/processors/runtime-input-processor.dtsi>

&trackball_central_listener {
    status = "okay";
    device = <&trackball_central>;
    input-processors = <&mouse_runtime_input_processor>;

    scroller {
        layers = <3 4 5>;   // NUM/NAV_MAC/NAV_WIN（実 config と同じ）
        input-processors =
            <&zip_xy_transform INPUT_TRANSFORM_X_INVERT
             &zip_xy_to_scroll_mapper
             &zip_scroll_transform INPUT_TRANSFORM_X_INVERT
             &zip_scroll_scaler 1 5
             &scroll_runtime_input_processor>;
    };
};
```

補足:
- 現在の `mona2_r.overlay` は、既存の `zip_*` 変換を維持しつつ `&scroll_runtime_input_processor` を追加する構成。さらに慣性スクロール・パン（layer 8）・ジェスチャー（layer 9/10）のサブノードも持つ（実 config 参照）。
- `mona2.keymap` の `#define ZMK_POINTING_DEFAULT_SCRL_VAL`（実 config では `30`）を大きくしすぎると、環境によっては `pointing.h` 側定義との再定義 warning が出る場合がある。
