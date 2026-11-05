/*
 * BT プロファイルに合わせてベース層 (MAC / WIN) を自動で切り替える。
 *
 * 背景: ベース層は BLE 層の bt_mac0 / bt_win1 / bt_win2 マクロ
 * (&to <層> &bt BT_SEL n) で切り替えているが、層の状態はフラッシュに保存されない。
 * 右手 (central) が再起動すると BT プロファイルは保存値 (例: BT1=Win) に戻るのに、
 * ベース層だけ既定の 0 (MAC) に戻ってしまい、Windows に Mac 配列で打つことになる。
 *
 * ここでは「アクティブな BT プロファイルの番号が変わったとき」(起動後の初回を含む)
 * に、マクロと同じ対応表でベース層を合わせ直す。
 * 同じプロファイルへの切断→再接続では何もしない (O24 トグル等を消さないため)。
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include <zmk/event_manager.h>
#include <zmk/events/ble_active_profile_changed.h>
#include <zmk/keymap.h>

LOG_MODULE_REGISTER(mona2_profile_base_layer, CONFIG_ZMK_LOG_LEVEL);

/* config/mona2.keymap の #define と揃えること */
#define LAYER_MAC 0
#define LAYER_WIN 1
#define LAYER_NONE 0xFF

/* プロファイル番号 → ベース層。bt_mac0 / bt_win1 / bt_win2 マクロと同じ対応。
 * 表にない番号 (BT3 / BT4) は層を変えない (従来どおり) */
static const uint8_t profile_layers[] = {LAYER_MAC, LAYER_WIN, LAYER_WIN};

static uint8_t last_profile = 0xFF;

static int profile_base_layer_listener(const zmk_event_t *eh) {
    const struct zmk_ble_active_profile_changed *ev = as_zmk_ble_active_profile_changed(eh);
    if (ev == NULL) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    /* このイベントは同じプロファイルの接続・切断でも飛んでくるので、番号が変わったときだけ動く */
    if (ev->index == last_profile) {
        return ZMK_EV_EVENT_BUBBLE;
    }
    last_profile = ev->index;

    uint8_t layer = ev->index < ARRAY_SIZE(profile_layers) ? profile_layers[ev->index] : LAYER_NONE;
    if (layer == LAYER_NONE) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    /* マクロ経由の切替ではマクロ側の &to と二重になるが、結果は同じなので害はない */
    LOG_INF("BT profile %d -> base layer %d", ev->index, layer);
    zmk_keymap_layer_to(layer, false);

    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(mona2_profile_base_layer, profile_base_layer_listener);
ZMK_SUBSCRIPTION(mona2_profile_base_layer, zmk_ble_active_profile_changed);
