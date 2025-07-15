#!/bin/bash
# マイページ自動生成システム 起動スクリプト

echo "🚀 図書館マイページ自動生成システムを起動中..."
echo

# カレントディレクトリがプロジェクトルートかチェック
if [ ! -f "requirements.txt" ] || [ ! -f "web_api.py" ]; then
    echo "❌ プロジェクトルートディレクトリで実行してください"
    echo "   requirements.txt と web_api.py が見つかりません"
    exit 1
fi

# 仮想環境の作成・アクティベート
echo "� Python仮想環境をチェック中..."
if [ ! -d ".venv" ]; then
    echo "📦 仮想環境を作成中..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ 仮想環境の作成に失敗しました"
        echo "   python3が正しくインストールされているか確認してください"
        exit 1
    fi
    echo "✅ 仮想環境を作成しました"
fi

# 仮想環境をアクティベート
echo "🔄 仮想環境をアクティベート中..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 仮想環境のアクティベートに失敗しました"
    exit 1
fi

# 依存関係をインストール
echo "📦 Python依存関係をチェック中..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 依存関係のインストールに失敗しました"
    exit 1
fi

# ディレクトリ構造をチェック
echo "📂 ディレクトリ構造をチェック中..."
if [ ! -d "data" ]; then
    echo "📁 dataディレクトリを作成しています..."
    mkdir -p data
fi

if [ ! -d "src" ]; then
    echo "❌ srcディレクトリが見つかりません"
    exit 1
fi

if [ ! -d "scripts" ]; then
    echo "❌ scriptsディレクトリが見つかりません"
    exit 1
fi

if [ ! -d "temp_uploads" ]; then
    echo "📁 temp_uploadsディレクトリを作成しています..."
    mkdir -p temp_uploads
fi

echo "✅ すべてのチェックが完了しました"
echo

# Webサーバーを起動
echo "🌐 Webサーバーを起動中..."
echo "📱 管理画面: http://localhost:8080"
echo "🛑 終了するには Ctrl+C を押してください"
echo

python web_api.py
