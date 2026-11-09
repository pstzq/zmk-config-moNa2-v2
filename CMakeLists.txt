# このリポジトリ自体を Zephyr モジュールとして読み込ませ、小さな独自コードを足す
if(CONFIG_MONA2_INPUT_PROCESSOR_SPEED_ACCEL)
    target_sources(app PRIVATE src/input_processor_speed_accel.c)
endif()
