#!/usr/bin/env python3
"""
マイページ自動生成システムのテストスクリプト
"""

import os
import sys
import subprocess
import json

def test_mypage_generation():
    """マイページ生成をテスト"""
    
    print("=== マイページ自動生成システム テスト ===\n")
    
    # スクリプトのパス
    script_path = "scripts/generate_mypage.py"
    tsv_path = "data/tsv_WQx333yUurmoVMy7TVsmIlKNrdVWAQ.txt"
    
    # ファイルの存在確認
    if not os.path.exists(script_path):
        print(f"エラー: {script_path} が見つかりません")
        return False
    
    if not os.path.exists(tsv_path):
        print(f"エラー: {tsv_path} が見つかりません")
        return False
    
    print("1. 既存のAmane KuboのTSVデータを使用してマイページを再生成...")
    
    # マイページ生成コマンド
    cmd = [
        "python3", script_path,
        tsv_path,
        "--user-id", "amane_test",
        "--name", "Amane Kubo (Auto-generated)",
        "--position", "東京大学 大学院工学系研究科 M2 (自動生成)",
        "--avatar", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&h=300&fit=crop&crop=face"
    ]
    
    try:
        # コマンド実行
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ マイページ生成成功!")
            print(result.stdout)
            
            # 生成されたファイルの確認
            generated_html = "src/mypage_amane_test.html"
            users_json = "data/users.json"
            
            if os.path.exists(generated_html):
                print(f"✅ HTMLファイル生成確認: {generated_html}")
            else:
                print(f"❌ HTMLファイル未生成: {generated_html}")
            
            if os.path.exists(users_json):
                print(f"✅ ユーザーデータ更新確認: {users_json}")
                
                # users.jsonの内容確認
                with open(users_json, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    user_ids = [user['id'] for user in users_data['users']]
                    print(f"   登録ユーザー数: {len(users_data['users'])}")
                    print(f"   ユーザーID一覧: {user_ids}")
                    
                    # 新しく生成されたユーザーを確認
                    new_user = next((u for u in users_data['users'] if u['id'] == 'amane_test'), None)
                    if new_user:
                        print(f"✅ 新規ユーザー追加確認: {new_user['name']}")
                        print(f"   総文献数: {new_user['stats']['totalBooks']}")
                        print(f"   今年の文献数: {new_user['stats']['thisYearBooks']}")
                        print(f"   専門分野: {', '.join(new_user['specializations'])}")
                    else:
                        print("❌ 新規ユーザーがusers.jsonに見つかりません")
            else:
                print(f"❌ ユーザーデータファイル未生成: {users_json}")
            
            return True
            
        else:
            print("❌ マイページ生成失敗!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def test_network_integration():
    """ネットワーク統合をテスト"""
    
    print("\n2. ネットワーク統合テスト...")
    
    users_json = "data/users.json"
    if not os.path.exists(users_json):
        print(f"❌ {users_json} が見つかりません")
        return False
    
    try:
        with open(users_json, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        print("✅ users.jsonの読み込み成功")
        print(f"   ユーザー数: {len(users_data['users'])}")
        print(f"   カテゴリ数: {len(users_data['categories'])}")
        
        # ネットワーク接続の確認
        for user in users_data['users']:
            if 'networkConnections' in user:
                print(f"   {user['name']}: {len(user['networkConnections'])} 接続")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def test_html_integration():
    """HTML統合をテスト"""
    
    print("\n3. HTML統合テスト...")
    
    html_files = [
        "src/my_library.html",
        "src/map.html", 
        "src/network_graph.html",
        "src/mypage.html",
        "src/mypage_amane.html"
    ]
    
    js_file = "src/js/user_manager.js"
    
    # JavaScriptファイルの確認
    if os.path.exists(js_file):
        print(f"✅ ユーザーマネージャー確認: {js_file}")
    else:
        print(f"❌ ユーザーマネージャー未発見: {js_file}")
        return False
    
    # HTMLファイルの確認
    for html_file in html_files:
        if os.path.exists(html_file):
            print(f"✅ HTMLファイル確認: {html_file}")
            
            # user_manager.jsの読み込み確認
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "user_manager.js" in content:
                    print(f"   ✅ user_manager.js読み込み確認")
                else:
                    print(f"   ❌ user_manager.js読み込み未確認")
        else:
            print(f"❌ HTMLファイル未発見: {html_file}")
    
    return True

def main():
    """メインテスト実行"""
    
    print("マイページ自動生成システムの統合テストを開始します...\n")
    
    tests = [
        ("マイページ生成", test_mypage_generation),
        ("ネットワーク統合", test_network_integration), 
        ("HTML統合", test_html_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"テスト: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print(f"\n{'='*50}")
    print("テスト結果サマリー")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n合計: {passed}/{total} テスト成功")
    
    if passed == total:
        print("\n🎉 すべてのテストが成功しました!")
        print("\n次のステップ:")
        print("1. ブラウザでsrc/my_library.htmlを開く")
        print("2. ユーザー選択ドロップダウンをテスト")
        print("3. 新しく生成されたmypage_amane_test.htmlを確認")
        print("4. network_graph.htmlで動的ユーザー読み込みをテスト")
    else:
        print(f"\n⚠️  {total - passed}個のテストが失敗しました。上記のエラーを確認してください。")

if __name__ == "__main__":
    main()
