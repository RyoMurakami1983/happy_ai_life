# Security Policy

## 目的

この文書は、`happy_ai_life` で secret 漏洩またはその疑いが発生したときの標準対応手順を定義します。

ここでいう secret には、API key、access token、password、private key、接続文字列、GitHub Secrets に入る値、誤って commit された認証情報を含みます。

## 報告方法

- **公開 Issue / PR / Discussion / コメントには secret を貼らないでください。**
- まず repository owner へ **非公開チャネルで連絡**してください。
- GitHub の private vulnerability reporting / Security Advisory を使える場合は、それを優先してください。
- 使えない場合は、repository owner に直接連絡し、少なくとも次を共有してください。
  - いつ見つけたか
  - どの secret / system に関係するか
  - どこに露出したか（working tree、commit、PR、GitHub Actions log、外部共有先など）
  - まだ有効そうか、すでに無効化したか

## 初動

1. **公開拡散を止める**  
   新しい push、fork 共有、ログ転載、スクリーンショット共有を止めます。

2. **secret を再利用しない**  
   漏洩した値をそのまま使い続けないでください。

3. **gitleaks の検出結果を確認する**  
   pre-commit、pre-push、GitHub Actions の `gitleaks`、または手動の `gitleaks detect` が指した場所を特定します。

4. **関係者へ即時共有する**  
   repo owner と secret の所有者に、公開場所と影響範囲を伝えます。

## gitleaks 検出時の初動

`gitleaks` で止まった場合も、「まだ push されていないから安全」とは見なしません。  
端末履歴、スクリーン共有、ログ、別 branch への commit などに残っている可能性があります。

最低限、次を行います。

1. 検出された値が本物の secret か確認する。
2. 本物なら **無効化 / rotation を先に計画**する。
3. commit 前に止まった場合でも、ローカル履歴・一時ファイル・他 branch への混入を確認する。
4. push 後に検出した場合は、公開済みとして扱って報告と遮断を優先する。

## secret の無効化と rotation

1. **漏洩した secret を無効化**する。  
   API key revoke、token revoke、password reset、credential disable を最優先で行います。

2. **新しい secret を発行して rotation**する。  
   新しい値は GitHub Secrets、環境変数、または正規の secret store に再登録します。

3. **依存先を更新**する。  
   アプリ設定、CI/CD、MCP、外部サービス連携、ローカル `.env` などの古い値を置き換えます。

4. **古い値が使えないことを確認**する。  
   revoke 失敗や複数 credential の取り残しがないかを確認します。

## 履歴確認

secret がどこまで露出したかを確認します。

- 現在の working tree
- commit 履歴
- open / closed PR
- GitHub Actions logs
- issue / comment / discussion
- release artifact、cache、外部共有済みファイル

必要に応じて、`gitleaks detect --source . --verbose` などで repository 全体を再確認します。

## 影響調査

次を確認します。

- どの system / environment で使われる secret か
- 読み取り専用か、書き込み・管理権限があるか
- いつからいつまで有効だった可能性があるか
- 不正利用の兆候があるか
- 他の secret や派生 credential も巻き添えになっていないか

権限が広い secret、長期有効 token、production credential は **高優先度 incident** として扱います。

## 修復と再発防止

1. secret を source code、docs、test fixture、sample file に残さない。
2. 必要なら影響 commit / artifact / log を関係者確認の上で整理する。
3. `.gitleaks.toml` の allowlist 追加で隠す前に、まず本当に secret でないか確認する。
4. 再発理由を記録し、必要なら docs / hook / workflow / review 手順を修正する。
5. 同種の secret を持つ他 repository や環境にも横展開確認を行う。

## やってはいけないこと

- `--no-verify` で secret scan を回避したまま進める
- 公開コメントで secret 本文を共有する
- revoke 前に「たぶん大丈夫」と判断して放置する
- `.gitleaks.toml` の allowlist で incident を隠す
- security policy を弱める変更を incident 対応に紛れ込ませる

## 公開 vulnerability 報告について

- 一般的な脆弱性報告は GitHub Security Advisory または repository owner への非公開連絡で受け付けます。
- 実 secret が含まれる場合は、公開 issue ではなく必ず非公開チャネルを使ってください。

## 関連

- [品質ゲート](docs/QUALITY_GATES.md)
- [Enterprise Security](docs/ENTERPRISE_SECURITY.md)
- [Trust Boundary](docs/TRUST_BOUNDARY.md)
- [Hooks Governance](docs/HOOKS_GOVERNANCE.md)
