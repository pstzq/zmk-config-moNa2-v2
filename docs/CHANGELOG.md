# 変更履歴

このファイルはキーマップ設計・ドキュメントへの変更を記録します。
実装ファイル（`.keymap` / `.overlay` / `.conf`）の変更はコミットログを参照してください。

フォーマット：
```
## YYYY-MM-DD  タイトル
- 変更内容（by GitHub 編集 / by チャット依頼）
```

---

## 2026-06-10  ドキュメント最新化（実装との乖離修正・README2.md 廃止）

（by チャット依頼）

### README.md
- Layer 表 行9・10 の起動方法を修正: `Del 長押し` → `Q 長押し`
- Layer 表 行11 CURSOR の起動方法を修正: `Q 長押し（誤）` → `未実装（予約済み）`
- Layer 12 O24（`Q`+`P` トグル）を Layer 表に追加
- トラックボール機能表を修正: Q長押し→ウィンドウスナップ、Del 行を削除
- ウィンドウスナップ節の操作キーを修正: `Del` → `Q`
- DYA Studio セクションのリンク先を `README2.md` → `docs/keymap-phase1.md` に変更
- `boards/shields/mona2/mona2.keymap` が旧デフォルトである旨の補足を末尾に追加

### docs/keymap-phase1.md
- 冒頭のブランチ名記述（`claude/keymap-rework`）を削除し「設計・実装ドキュメント」に変更
- Layer 表に Layer 11（CURSOR、未実装）・Layer 12（O24）を追加
- `inertial-scroll-threshold` の値を修正: `<4>` → `<8>`（`mona2_r.overlay` と一致）
- Phase 2 共通前提の Layer 番号記述を修正: `0〜10` → Layer 11/12 が実装済みの実態に合わせる

### README2.md
- `old/README2.md` に移動（廃止）。内容は `docs/keymap-phase1.md` に包含済み。
