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

```yaml
manifest:
  remotes:
    - name: cormoran
      url-base: https://github.com/cormoran
    - name: badjeff
      url-base: https://github.com/badjeff

  projects:
    - name: zmk
      remote: cormoran
      revision: v0.3-branch+dya
      import: app/west.yml

    - name: zmk-module-ble-management
      remote: cormoran
      revision: main

    - name: zmk-module-battery-history
      remote: cormoran
      revision: main

    - name: zmk-module-settings-rpc
      remote: cormoran
      revision: main

    - name: zmk-module-runtime-input-processor
      remote: cormoran
      revision: main

    - name: zmk-behavior-runtime-sensor-rotate
      remote: cormoran
      revision: main

    - name: zmk-pmw3610-driver
      remote: badjeff
      revision: zmk-0.3

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
        layers = <3>;
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
- 現在の `mona2_r.overlay` は、既存の `zip_*` 変換を維持しつつ `&scroll_runtime_input_processor` を追加する構成。
- `mona2.keymap` に `#define ZMK_POINTING_DEFAULT_SCRL_VAL 100` を置くと、環境によっては `pointing.h` 側定義との再定義 warning が出る場合がある。
