#!/usr/bin/env python3
"""
マイページ自動生成システム用のWebAPI
フロントエンドからのリクエストを受け取り、TSVファイルを処理してマイページを生成
"""

from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
import os
import tempfile
import threading
import time
import json
from werkzeug.utils import secure_filename
import sys
import subprocess
from pathlib import Path
import venv
import platform

app = Flask(__name__)
CORS(app)  # CORS対応

# プロジェクトルートディレクトリを取得
PROJECT_ROOT = Path(__file__).parent.absolute()

# 設定（相対パスを使用）
UPLOAD_FOLDER = PROJECT_ROOT / 'temp_uploads'
DATA_FOLDER = PROJECT_ROOT / 'data'
SRC_FOLDER = PROJECT_ROOT / 'src'
SCRIPTS_FOLDER = PROJECT_ROOT / 'scripts'
VENV_FOLDER = PROJECT_ROOT / '.venv'

ALLOWED_EXTENSIONS = {'tsv', 'txt'}

# 必要なディレクトリを作成
for folder in [UPLOAD_FOLDER, DATA_FOLDER, SRC_FOLDER, SCRIPTS_FOLDER]:
    folder.mkdir(exist_ok=True)

# Python実行可能ファイルのパスを動的に取得
def get_python_executable():
    """現在の環境のPython実行可能ファイルパスを取得"""
    
    # 仮想環境が存在する場合
    if VENV_FOLDER.exists():
        if platform.system() == "Windows":
            python_path = VENV_FOLDER / "Scripts" / "python.exe"
        else:
            python_path = VENV_FOLDER / "bin" / "python"
        
        if python_path.exists():
            return str(python_path)
    
    # システムのPython3を使用
    return sys.executable

# 処理状況を保存するグローバル変数
processing_status = {
    'is_processing': False,
    'progress': 0,
    'message': '',
    'logs': [],
    'error': None
}

def allowed_file(filename):
    """許可されたファイル形式かチェック"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_message(message, level='info'):
    """ログメッセージを追加"""
    global processing_status
    timestamp = time.strftime('%H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'level': level
    }
    processing_status['logs'].append(log_entry)
    print(f"[{timestamp}] {message}")

def update_progress(progress, message):
    """進行状況を更新"""
    global processing_status
    processing_status['progress'] = progress
    processing_status['message'] = message
    log_message(message)

@app.route('/')
def index():
    """インデックスページ（admin_dashboard.html）を返す"""
    return send_from_directory(SRC_FOLDER, 'admin_dashboard.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """srcディレクトリ内の静的ファイル（HTMLなど）を提供"""
    # 生成されたマイページもここに含まれる
    return send_from_directory(SRC_FOLDER, filename)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """TSVファイルのアップロードとマイページ生成"""
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': '別の処理が実行中です'}), 400
    
    # ファイルチェック
    if 'file' not in request.files:
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '許可されていないファイル形式です'}), 400
    
    # フォームデータを取得
    user_id = request.form.get('user_id')
    user_name = request.form.get('user_name')
    position = request.form.get('position')
    email = request.form.get('email', '')
    avatar_url = request.form.get('avatar_url', '')
    
    if not all([user_id, user_name, position]):
        return jsonify({'error': '必須項目が不足しています'}), 400
    
    # ファイルを保存
    filename = secure_filename(file.filename)
    temp_filepath = os.path.join(UPLOAD_FOLDER, f"{user_id}_{filename}")
    file.save(temp_filepath)
    
    # バックグラウンドで処理を開始
    thread = threading.Thread(
        target=process_mypage_generation,
        args=(temp_filepath, user_id, user_name, position, email, avatar_url)
    )
    thread.start()
    
    return jsonify({'message': '処理を開始しました', 'status': 'started'})

def process_mypage_generation(tsv_path, user_id, user_name, position, email, avatar_url):
    """マイページ生成処理（バックグラウンド実行）"""
    global processing_status
    
    try:
        processing_status['is_processing'] = True
        processing_status['progress'] = 0
        processing_status['logs'] = []
        processing_status['error'] = None
        
        update_progress(10, f'ユーザー {user_name} の処理を開始...')
        
        # Pythonスクリプトのコマンドを構築（相対パスを使用）
        python_executable = get_python_executable()
        generate_script = SCRIPTS_FOLDER / 'generate_mypage.py'
        
        cmd = [
            python_executable,
            str(generate_script),
            tsv_path,
            '--user-id', user_id,
            '--name', user_name,
            '--position', position
        ]
        
        if avatar_url:
            cmd.extend(['--avatar', avatar_url])
        
        update_progress(20, 'generate_mypage.pyスクリプトを実行中...')
        
        # スクリプトを実行（プロジェクトルートディレクトリで実行）
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        update_progress(60, 'スクリプト実行完了、結果を確認中...')
        
        if result.returncode == 0:
            update_progress(80, 'マイページ生成成功')
            log_message(result.stdout, 'success')
            
            # 生成されたファイルを確認（相対パスを使用）
            mypage_file = SRC_FOLDER / f'mypage_{user_id}.html'
            if mypage_file.exists():
                update_progress(90, f'マイページファイル確認: {mypage_file.name}')
            
            # users.jsonの更新を確認（相対パスを使用）
            users_json_file = DATA_FOLDER / 'users.json'
            if users_json_file.exists():
                update_progress(95, 'users.json更新確認')
            
            update_progress(100, f'✅ {user_name} のマイページ生成完了！')
            
        else:
            processing_status['error'] = result.stderr
            log_message(f'エラー: {result.stderr}', 'error')
            update_progress(100, f'❌ マイページ生成失敗')
            
    except Exception as e:
        processing_status['error'] = str(e)
        log_message(f'予期しないエラー: {str(e)}', 'error')
        update_progress(100, f'❌ 処理中にエラーが発生')
        
    finally:
        # 一時ファイルを削除
        try:
            os.remove(tsv_path)
            log_message(f'一時ファイル削除: {tsv_path}')
        except:
            pass
        
        # 少し待ってからフラグをリセット
        time.sleep(2)
        processing_status['is_processing'] = False

@app.route('/api/status', methods=['GET'])
def get_status():
    """処理状況を取得"""
    return jsonify(processing_status)

@app.route('/api/users', methods=['GET'])
def get_users():
    """登録ユーザー一覧を取得"""
    try:
        users_json_file = DATA_FOLDER / 'users.json'
        with open(users_json_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        return jsonify(users_data.get('users', []))
    except FileNotFoundError:
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/delete', methods=['POST'])
def delete_user():
    """ユーザー情報を削除する"""
    data = request.get_json()
    user_id_to_delete = data.get('user_id')

    if not user_id_to_delete:
        return jsonify({'error': 'ユーザーIDが指定されていません'}), 400

    try:
        # 1. users.jsonからユーザーを削除
        users_json_file = DATA_FOLDER / 'users.json'
        if users_json_file.exists():
            with open(users_json_file, 'r+', encoding='utf-8') as f:
                users_data = json.load(f)
                initial_len = len(users_data['users'])
                users_data['users'] = [u for u in users_data['users'] if u.get('id') != user_id_to_delete]
                
                if len(users_data['users']) < initial_len:
                    f.seek(0)
                    f.truncate()
                    json.dump(users_data, f, indent=2, ensure_ascii=False)
                else:
                    return jsonify({'error': '指定されたユーザーが見つかりません'}), 404

        # 2. 対応するマイページHTMLを削除
        mypage_file = SRC_FOLDER / f'mypage_{user_id_to_delete}.html'
        if mypage_file.exists():
            os.remove(mypage_file)

        return jsonify({'message': f'ユーザー {user_id_to_delete} を削除しました'}), 200

    except Exception as e:
        return jsonify({'error': f'削除処理中にエラーが発生しました: {str(e)}'}), 500

@app.route('/api/reset', methods=['POST'])
def reset_processing():
    """処理状況をリセット"""
    global processing_status
    processing_status = {
        'is_processing': False,
        'progress': 0,
        'message': '',
        'logs': [],
        'error': None
    }
    return jsonify({'message': '処理状況をリセットしました'})

if __name__ == '__main__':
    print("🚀 マイページ自動生成システム WebAPI を起動中...")
    print("📝 管理画面: http://localhost:8080")
    print("🔗 API エンドポイント:")
    print("   - POST /api/upload: ファイルアップロード")
    print("   - GET  /api/status: 処理状況取得")
    print("   - GET  /api/users:  ユーザー一覧取得")
    print("   - POST /api/reset:  処理状況リセット")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=8080)
    print("🚀 マイページ自動生成システム WebAPI を起動中...")
    print("📝 管理画面: http://localhost:8080")
    print("🔗 API エンドポイント:")
    print("   - POST /api/upload: ファイルアップロード")
    print("   - GET  /api/status: 処理状況取得")
    print("   - GET  /api/users:  ユーザー一覧取得")
    print("   - POST /api/reset:  処理状況リセット")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=8080)
    
    app.run(debug=True, host='0.0.0.0', port=8080)
