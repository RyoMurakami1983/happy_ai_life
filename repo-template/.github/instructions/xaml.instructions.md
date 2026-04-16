---
description: XAML / WPF View 向けの追加ルール
applyTo: "**/*.xaml,**/*.xaml.cs"
---

# XAML / WPF instructions

- [repository-wide instructions](../copilot-instructions.md) を前提とし、このファイルは XAML / WPF View に閉じた局所ルールだけを定義する。
- WPF / XAML / binding を触るときは、実装前にまず `dotnet` を入口として思い出し、必要なら `dotnet-wpf-mvvm-patterns` を参照する。
- View は binding、layout、visual state に集中し、業務ロジック、I/O、永続化、プロトコル処理は ViewModel または service に置く。
- user input 以外の binding は既定で `OneWay` と考え、`TextBox.Text` など既定で `TwoWay` のプロパティに読み取り専用 property を bind する場合は `Mode=OneWay` を明示する。
- user action は event handler より command を優先し、CanExecute と busy state を ViewModel 側で表現する。
- ViewModel / DataContext の所有者は明示し、暗黙の Service Locator や code-behind からの隠れた解決を避ける。
- validation、status、error message は ViewModel の状態として公開し、XAML 側で文字列組み立てや分岐ロジックを増やしすぎない。
- focus を奪う UI、Clipboard、UI Automation、外部アプリ連携が絡む場合は、見た目の完成より先に target capture、foreground 制御、fallback を確認する。
- code-behind は framework glue に限定し、UI 振る舞いの主制御を置かない。
