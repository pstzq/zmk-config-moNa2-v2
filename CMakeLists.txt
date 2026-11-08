# このリポジトリ自体を Zephyr モジュールとして読み込ませ、小さな独自コードを足す
if(CONFIG_MONA2_PROFILE_BASE_LAYER)
    target_sources(app PRIVATE src/profile_base_layer.c)
endif()
