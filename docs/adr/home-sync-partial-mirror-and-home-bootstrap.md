# home sync を diff-based safe sync にし HOME bootstrap package を配布する

**日付**: 2026-04-15  
**ステータス**: 承認

---

## 背景

`sync-to-home.ps1` は once partial-mirror として設計され、`skills/` と `agents/` も managed directory として template 一致へ寄せていた。  
この方針は drift 抑制には有効だった一方で、配布後の user-owned extra skill / agent を不用意に削除しうるため、HOME 環境の拡張点として危険だった。

また downstream repo の安全弁不足を補うには、母艦 repo が手元に無い状態でも `repo-template/`、Copilot hooks、bootstrap script を HOME 側から使える必要があった。

## 判断

- home sync は **filesystem diff ベース**に切り替える
- `skills/` は skill directory 単位で比較し、extra skill は保持する
- `agents/` は `*.agent.md` 単位で比較し、extra agent は保持する
- `skills/` / `agents/` で同名更新が必要な場合は、更新前の内容を `%USERPROFILE%\copilot_archives\...` に 1 世代だけ退避してから置き換える
- 次の managed surface は template 一致へ同期し、extra item を削除する
  - `repo-template/`
  - `.github/hooks/`
- 次は削除しない copy-only / user-owned 領域として維持する
  - `docs/furikaeri/`
  - `mcp-config.json`
  - その他 runtime data
- HOME 側には bootstrap package として以下を配布する
  - `repo-template/`
  - `.github/hooks/`
  - `scripts/sync-to-repo.ps1`
  - `scripts/install-git-hooks.ps1`
  - `scripts/repo-secure-check.ps1`
  - `scripts/home_sync_planner.py`
- downstream repo の不足判定は `repo-secure-check` を正本にし、launcher や skill はその結果を使う
- Branch Protection / Ruleset はローカルでは確実に判定できないため、bootstrap 条件ではなく warning とする

## 根拠

- `skills/` と `agents/` は HOME 側の拡張点でもあるため、extra item を保持しないと配布後の独自資産を壊す
- runtime data / user-owned extra / managed surface を分けることで、削除境界を説明しやすくなる
- 更新前 archive を 1 世代だけ残せば、事故時の手動復元経路を最小コストで確保できる
- HOME 側 bootstrap package を持てば、mother ship repo を開いていない状態でも downstream repo の初期安全弁を配布できる
- `repo-secure-check` を単一入口にすると、launcher・skill・将来の hook で同じ判定契約を再利用できる

## トレードオフ

| 選択肢 | 利点 | 欠点 |
| --- | --- | --- |
| whitelist copy のまま維持 | runtime data 保護が単純 | managed surface が drift しやすい |
| home 全体を mirror | HOME と template を強く一致させられる | user-owned file / extra skill / extra agent を巻き込みやすい |
| **skills/agents preserve + managed surface diff sync** | user-owned extra を壊さず drift を抑えやすい | 同期単位が複数になり実装は複雑になる |

## 運用

- `sync-to-home.ps1` の dry-run / 実行ログで、skills/agents の archive 付き差分同期と managed surface を区別して示す
- `repo-bootstrap` は `repo-secure-check` の結果を見て、不足がある場合だけ dry-run 既定で提案する
- 実適用時は `sync-to-repo.ps1` と `install-git-hooks.ps1` を順に実行し、local safety valve をそろえる

## 関連

- `docs/adr/home-sync-whitelist.md`
- `docs/adr/main-branch-protection-and-githooks.md`

## 補遺: plugin source-of-truth への移行

この ADR の `skills/` / `agents/` diff sync と `scripts/home_sync_planner.py` 配布は、Copilot CLI plugin marketplace 方式を primary path にした後は採用しない。

現在の home sync は、`repo-template/`、`.github/hooks/`、repo bootstrap scripts、`copilot-instructions.md` の最小 bootstrap に限定する。reusable skills / agents の正本は `plugins/happy-ai-life/` に移り、開発者自身も plugin install で利用する。
