# GUI Debug Module

Use this module when the failure involves rendering, layout, focus, selection, input handling, or editor behavior.

This module starts slightly ahead of the others because the first source material came from GUI debugging, but it should still grow only from real sessions.

## Current Focus

- **Evidence**: screenshots, DOM or HTML snapshots, input scripts, bounding boxes, visual diffs
- **Fault boundaries**: input handling, selection or caret state, document mutation, layout recomputation, persistence, CSS layer
- **Repro levers**: same key sequence, same mode, same browser, same viewport, same local state
- **Quality gate**: the same visible scenario behaves the same way before and after in every affected mode
- **WPF note**: for blank screens, confirm the `.xaml` and `.xaml.cs` pair together before blaming bindings or navigation

## WPF Blank Screen — 初動チェックリスト

WPF で画面が白くなる（またはコンテンツが表示されない）場合、次の順序で確認する。

### 1. `.xaml` / `.xaml.cs` ペア確認

- [ ] 対象 View の `.xaml` ファイルが存在するか
- [ ] 対応する `.xaml.cs` (code-behind) が同じ名前空間 / 同じディレクトリにあるか
- [ ] `.xaml.cs` の partial class 名が `.xaml` の `x:Class` と一致しているか
- [ ] `.csproj` に `.xaml` が `<Page Include="...">` として登録されているか

### 2. `InitializeComponent()` 呼び出し確認

- [ ] code-behind コンストラクタで `InitializeComponent()` が呼ばれているか
- [ ] `InitializeComponent()` より前に例外が起きていないか（コンストラクタを丸ごと try/catch で囲んで確認）

### 3. DataTemplate / ContentControl 登録

- [ ] `ResourceDictionary` または `App.xaml` に対象 ViewModel → View の DataTemplate が登録されているか
- [ ] `ContentControl.Content` または `Frame.Content` に ViewModel インスタンスが渡されているか
- [ ] `DataType` が正しい型を指しているか（大文字小文字、名前空間）

### 4. Navigation Route

- [ ] 画面遷移ロジックで正しい型が Push / Navigate されているか
- [ ] Navigate メソッドの引数に View インスタンスではなく ViewModel を渡す設計の場合、変換が行われているか

### 5. App Resources 依存

- [ ] 白画面を起こすコントロールが参照する StaticResource / DynamicResource が App.xaml / Merged Dictionary に存在するか
- [ ] リソースキーのスペルミスがないか（ランタイムは KeyNotFoundException より静かに失敗する場合がある）

## WPF / MSTest — `testhost` DLL ロック時の対処

`dotnet test` 後に `testhost.exe` が DLL を握り続けると、次の `dotnet build` / `dotnet test` が MSB3026 retry で止まるように見える。白画面の根本原因と区別するために手順を明文化する。

### 症状の見分け方

| 観察 | 推定原因 |
|---|---|
| build は通るが test が "retry 1/5..." で止まる | testhost が DLL をロック中 |
| `dotnet build` 自体が MSB3026 エラーで失敗する | testhost または別のプロセスがビルド出力をロック中 |
| build は通り test も通るが UI は白 | コード原因（チェックリスト Step 1〜5 を確認） |

### 対処手順

1. **ロック中のプロセスを特定する**

   ```powershell
   Get-Process | Where-Object { $_.Name -like "testhost*" }
   ```

2. **明示的に停止する**

   ```powershell
   Stop-Process -Id <PID> -Force
   ```

3. **複数プロセスをまとめて停止する場合**

   ```powershell
   Get-Process | Where-Object { $_.Name -like "testhost*" } | Stop-Process -Force
   ```

4. **停止確認後に再実行**

   ```powershell
   # プロセスが消えたことを確認
   Get-Process | Where-Object { $_.Name -like "testhost*" }
   # 問題なければ再実行
   dotnet test
   ```

### 再実行前の確認ポイント

- `bin/` または `obj/` 配下の DLL タイムスタンプが最新ビルドと一致しているか
- 複数のテストプロジェクトが並行実行されていないか
- テスト実行時に `--no-build` を使う場合、ビルド成功後に限定するか

## CLI 検証が不安定なときの切り替え条件

CLI 側の証拠が収束しない場合に、Visual Studio F5 や手動確認へ切り替える判断基準。

### 切り替えのトリガー条件（いずれか 1 つ以上で切り替えを検討する）

- `dotnet test` が `testhost` ロック解消後も同じエラーを 3 回以上繰り返す
- CLI の出力が空または不完全で、UI の描画が起きたかどうか判断できない
- FlaUI / UI テスト自動化ツールが Window を見つけられず、ツール側の問題か UI 側の問題か切り分けられない
- ビルドは成功しているのに実行時に例外が出ず、かつ UI も白い（silent failure の可能性）

### 切り替え後に残す最低限の証拠

1. CLI での最後の実行コマンドと出力（エラーまたは空出力）
2. `testhost` 停止コマンドを実行したかどうかの記録
3. Visual Studio での F5 実行結果（例外ウィンドウ、Output、白画面のスクリーンショット）
4. ビルドログ（警告を含む）

### 完了条件の分岐

#### 根本原因が確定して close できる場合

- コード原因（例：`.xaml.cs` 欠落、`InitializeComponent()` 未呼び出し）を特定し、修正後に手動または自動で同じシナリオが正常動作したことを確認できた
- Visual Studio で F5 実行し、画面が正常に表示されたスクリーンショットまたは録画がある

#### 根本原因が未確定でも close できる場合

- 問題が再現しなくなった原因が環境リセット（`testhost` 停止、clean build）の可能性が高く、直近のコード変更との因果が確認できた
- 手動確認で症状が消えており、次の再発時のために checklist と手順を残してある

#### 追加調査が必要で close を保留する場合

- CLI と Visual Studio のどちらでも症状を安定再現できていない
- 症状が出る条件（順序、モード、入力）がまだ特定できていない
- 修正を入れたが、チェックリストの全項目を確認していない

## Growth Policy

Append new rules only after a real session proves they matter.

When you add a lesson, record:

1. The trigger shape that made the bug reproducible
2. The evidence that made the difference undeniable
3. The boundary that actually owned the bug
4. The verification step that prevented recurrence
