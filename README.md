# AudioSwitcher

Windows 11向けの常駐型アプリ別オーディオ出力スイッチャーです。音量ミキサーと同様に現在Audio Sessionを持つアプリを一覧から登録できます。アプリ、またはWindows全体の既定出力にグローバルショートカットを割り当て、登録順に出力デバイスを切り替えます。

## 開発環境

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

## 起動

```powershell
audio-switcher
```

初回起動時は設定画面が開きます。設定は `%APPDATA%\AudioSwitcher\config.json` に保存され、設定後はタスクトレイに常駐します。

設定画面のチェックボックスから、現在のWindowsユーザーのログイン時に自動起動するよう登録できます。管理者権限は不要です。

Windows全体の切替では通常音声向けのConsoleとMultimediaを同時に変更し、Communicationsの既定デバイスは変更しません。

## MVPの制限

- アプリ別切替には対象exeのアクティブなAudio Sessionが必要です。
- アプリが独自にWASAPIデバイスを直接選択している場合、Windowsのルーティング設定に追従しないことがあります。
- アプリ別Audio Policy APIおよびシステム既定変更のAPIは非公開です。Windows更新時の修正箇所は `platform/windows` 配下へ隔離しています。
