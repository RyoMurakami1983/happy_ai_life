# Host terminal font と WSL の切り分け

## 結論

Oh My Posh のアイコンは、statusline の renderer が動く OS ではなく、**実際に表示している terminal** が描画します。

- Windows で Copilot CLI を開く: Windows 側 terminal の font 設定を見る
- WSL で Copilot CLI を開く: **Windows host 側 terminal** の font 設定を見る

WSL 内にフォントを追加しても、Windows Terminal の `font.face` が Nerd Font でなければ glyph 崩れは残ります。

## 推奨フォント

Oh My Posh の推奨は `MesloLGM Nerd Font` です。

Windows で `oh-my-posh` が入っているなら、次で導入できます。

```powershell
oh-my-posh font install meslo
```

すでに `CaskaydiaMono Nerd Font` や他の Nerd Font を使っていて問題なく表示できるなら、そのままで構いません。

## Windows Terminal の設定例

全 profile に効かせる場合:

```json
{
  "profiles": {
    "defaults": {
      "font": {
        "face": "MesloLGM Nerd Font"
      }
    }
  }
}
```

WSL profile だけに効かせる場合:

```json
{
  "profiles": {
    "list": [
      {
        "name": "Ubuntu-24.04",
        "source": "Microsoft.WSL",
        "font": {
          "face": "MesloLGM Nerd Font"
        }
      }
    ]
  }
}
```

## 典型的な見え方

| 症状 | 原因のことが多い箇所 |
| --- | --- |
| Windows ではきれい、WSL では `??` や崩れた記号 | Windows Terminal の WSL profile に font が入っていない |
| PowerShell ではきれい、別 terminal では崩れる | terminal ごとに font 設定が違う |
| `oh-my-posh` は入っているのに icon が崩れる | `oh-my-posh` ではなく host terminal font の問題 |

## この skill の installer が見るもの

- `oh-my-posh` が PATH にいるか
- Windows Terminal の `settings.json` が見つかるか
- `profiles.defaults.font.face` または対象 profile の `font.face` が Nerd Font に見えるか
- host Windows に代表的な Nerd Font が入っていそうか

installer は **診断だけ** を行い、Windows Terminal の設定は自動変更しません。
理由は、terminal 全体へ影響する UI 設定であり、意図しない profile まで変える危険を避けるためです。
