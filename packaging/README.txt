TradeMirror Portable Edition

Start
-----
Double-click TradeMirror.exe. No Python, Node.js, npm, pip, or database installation is required.

Requirements
------------
- Windows 10/11 x64 with Microsoft Edge WebView2 Runtime.
- MetaTrader 5 is optional. It is required only for MT5 history synchronization and market-candle replay.

Data location
-------------
TradeMirror writes its database, candle cache, TMF files, import previews, and logs to:
%APPDATA%\TradeMirror\

Removing this extracted folder removes the application only. Delete the AppData folder separately if you also want to remove your local data.

Security
--------
TradeMirror is a read-only trading analyzer. It reads closed trade history and market data only; it does not place orders, modify positions, or collect MT5 credentials.

Troubleshooting
---------------
If startup fails, check:
%APPDATA%\TradeMirror\logs\engine\engine.log
