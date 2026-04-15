# home sync を partial-mirror 化し HOME bootstrap package を配布する

**日付**: 2026-04-15  
**ステータス**: 承認

---

## 背景

`sync-to-home.ps1` は whitelist copy として設計され、HOME 側の extra file を保持していた。  
この方針は runtime data 保護には有効だった一方で、`skills/` と `agents/` のような managed directory では template と HOME がずれ続け、dry-run の見え方と実行後の期待が食い違いやすかった。

また downstream repo の安全弁不足を補うには、母艦 repo が手元に無い状態でも `repo-template/`、Copilot hooks、bootstrap script を HOME 側から使える必要があった。

## 判断

- home sync は **partial-mirror** に切り替える
- 次の managed directory は template 一致へ同期し、extra item を削除する
  - `skills/`
  - `agents/`
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
- downstream repo の不足判定は `repo-secure-check` を正本にし、launcher や skill はその結果を使う
- Branch Protection / Ruleset はローカルでは確実に判定できないため、bootstrap 条件ではなく warning とする

## 根拠

- `skills/` と `agents/` は managed content なので、template と HOME が一致しているほうが運用しやすい
- runtime data と managed content を分けることで、削除境界を説明しやすくなる
- HOME 側 bootstrap package を持てば、mother ship repo を開いていない状態でも downstream repo の初期安全弁を配布できる
- `repo-secure-check` を単一入口にすると、launcher・skill・将来の hook で同じ判定契約を再利用できる

## トレードオフ

| 選択肢 | 利点 | 欠点 |
| --- | --- | --- |
| whitelist copy のまま維持 | runtime data 保護が単純 | managed directory が drift しやすい |
| home 全体を mirror | HOME と template を強く一致させられる | user-owned file や runtime data を巻き込みやすい |
| **managed directory だけ partial-mirror** | drift 解消と user-owned 領域保護を両立しやすい | managed / user-owned の境界を明文化する必要がある |

## 運用

- `sync-to-home.ps1` の dry-run / 実行ログで、mirror-managed directory と copy-only 領域を区別して示す
- `repo-bootstrap` は `repo-secure-check` の結果を見て、不足がある場合だけ dry-run 既定で提案する
- 実適用時は `sync-to-repo.ps1` と `install-git-hooks.ps1` を順に実行し、local safety valve をそろえる

## 関連

- `docs/adr/home-sync-whitelist.md`
- `docs/adr/main-branch-protection-and-githooks.md`
