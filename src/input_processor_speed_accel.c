/*
 * トラックボールの速度連動加速 (Keyball の adjust_mouse_speed を ZMK の入力プロセッサへ移植)
 *
 * 元ネタ: mass (@mass_0X00) 氏の keyball.c 改造 (2023/08/20)
 *   movement_size = |x| + |y|
 *   movement_size が大きい (速く回した) ほど倍率を上げ、小さいほど下げる。
 *
 * ZMK との違い:
 *  - センサーの1レポートは REL_X と REL_Y の2イベントに分かれて流れてくる
 *    (X が先、sync=false。Y だけ/X だけのこともある)。
 *    X の時点では同じレポートの Y がまだ分からないので、直前レポートの |y| で代用する。
 *    Y の時点では同じレポートの |x| が分かるので正確に計算する。
 *  - float を使わず百分率の整数で計算し、端数は軸ごとに持ち越す。
 *    (0.2 倍などで 1 カウントの動きが毎回 0 に切り捨てられないように)
 *
 * 係数は boards/shields/mona2/mona2_r.overlay の speed_accel ノードで変更する。
 */

#define DT_DRV_COMPAT mona2_input_processor_speed_accel

#include <stdlib.h>
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/input/input.h>
#include <zephyr/sys/util.h>
#include <drivers/input_processor.h>

#include <zephyr/logging/log.h>

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

struct speed_accel_config {
    const uint32_t *thresholds;
    const uint32_t *multipliers;
    size_t len;
    uint32_t default_percent;
    uint32_t pair_timeout_ms;
};

struct speed_accel_data {
    int32_t rem_x;
    int32_t rem_y;
    /* 同じレポートの X (Y の計算用) */
    int32_t frame_x;
    bool frame_x_pending;
    /* 直前レポートの Y (X の計算用) */
    int32_t last_y;
    int64_t last_y_time;
};

static uint32_t pick_percent(const struct speed_accel_config *cfg, int32_t movement) {
    for (size_t i = 0; i < cfg->len; i++) {
        if (movement > (int32_t)cfg->thresholds[i]) {
            return cfg->multipliers[i];
        }
    }
    return cfg->default_percent;
}

static int32_t scale(int32_t value, uint32_t percent, int32_t *rem) {
    int32_t total = value * (int32_t)percent + *rem;
    int32_t out = total / 100;
    *rem = total - out * 100;
    return CLAMP(out, INT16_MIN, INT16_MAX);
}

static int speed_accel_handle_event(const struct device *dev, struct input_event *event,
                                    uint32_t param1, uint32_t param2,
                                    struct zmk_input_processor_state *state) {
    const struct speed_accel_config *cfg = dev->config;
    struct speed_accel_data *data = dev->data;

    if (event->type != INPUT_EV_REL) {
        return ZMK_INPUT_PROC_CONTINUE;
    }

    int64_t now = k_uptime_get();
    int32_t movement;
    int32_t *rem;

    if (event->code == INPUT_REL_X) {
        int32_t y = 0;
        if (!event->sync && (now - data->last_y_time) <= cfg->pair_timeout_ms) {
            /* このあと同じレポートの Y が来る。まだ分からないので直前の Y で代用 */
            y = data->last_y;
        }
        movement = abs(event->value) + abs(y);
        data->frame_x = event->value;
        data->frame_x_pending = !event->sync;
        rem = &data->rem_x;
    } else if (event->code == INPUT_REL_Y) {
        int32_t x = data->frame_x_pending ? data->frame_x : 0;
        movement = abs(x) + abs(event->value);
        data->frame_x_pending = false;
        data->last_y = event->value;
        data->last_y_time = now;
        rem = &data->rem_y;
    } else {
        return ZMK_INPUT_PROC_CONTINUE;
    }

    uint32_t percent = pick_percent(cfg, movement);
    int32_t in = event->value;
    event->value = scale(in, percent, rem);

    LOG_DBG("speed-accel code %d: %d (movement %d, %d%%) -> %d", event->code, in, movement,
            percent, event->value);

    return ZMK_INPUT_PROC_CONTINUE;
}

static const struct zmk_input_processor_driver_api speed_accel_driver_api = {
    .handle_event = speed_accel_handle_event,
};

#define SPEED_ACCEL_INST(n)                                                                        \
    BUILD_ASSERT(DT_INST_PROP_LEN(n, thresholds) == DT_INST_PROP_LEN(n, multipliers_percent),     \
                 "thresholds and multipliers-percent must have the same length");                 \
    static const uint32_t speed_accel_thresholds_##n[] = DT_INST_PROP(n, thresholds);              \
    static const uint32_t speed_accel_multipliers_##n[] = DT_INST_PROP(n, multipliers_percent);    \
    static struct speed_accel_data speed_accel_data_##n;                                           \
    static const struct speed_accel_config speed_accel_config_##n = {                              \
        .thresholds = speed_accel_thresholds_##n,                                                  \
        .multipliers = speed_accel_multipliers_##n,                                                \
        .len = DT_INST_PROP_LEN(n, thresholds),                                                    \
        .default_percent = DT_INST_PROP(n, default_percent),                                       \
        .pair_timeout_ms = DT_INST_PROP(n, pair_timeout_ms),                                       \
    };                                                                                             \
    DEVICE_DT_INST_DEFINE(n, NULL, NULL, &speed_accel_data_##n, &speed_accel_config_##n,           \
                          POST_KERNEL, CONFIG_KERNEL_INIT_PRIORITY_DEFAULT,                        \
                          &speed_accel_driver_api);

DT_INST_FOREACH_STATUS_OKAY(SPEED_ACCEL_INST)
