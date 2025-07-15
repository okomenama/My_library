#!/usr/bin/env python3
"""
TSVファイルからマイページを自動生成するAI
"""

import pandas as pd
import json
import re
import os
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Any
import argparse
from pathlib import Path


class MypageGenerator:
    def __init__(self, users_json_path: str = None):
        """マイページ生成器を初期化"""
        # プロジェクトルートディレクトリを取得
        self.project_root = Path(__file__).parent.parent
        
        # デフォルトのパスを設定（相対パス）
        if users_json_path is None:
            self.users_json_path = self.project_root / "data" / "users.json"
        else:
            self.users_json_path = Path(users_json_path)
            
        self.load_users_data()
        
        # 書籍分類のためのキーワードマッピング
        self.category_keywords = {
            "control-theory": ["制御", "ロバスト", "最適制御", "非線形", "システム制御"],
            "system-identification": ["システム同定", "同定", "部分空間", "パラメータ推定"],
            "data-assimilation": ["データ同化", "同化", "観測", "カルマン"],
            "meteorology": ["気象", "大気", "気候", "天気"],
            "numerical-weather": ["数値予報", "予報", "数値", "気象予測"],
            "fluid-dynamics": ["流体", "動力学", "非線形動力"],
            "mathematics": ["数学", "統計", "代数", "幾何", "確率", "統計力学"],
            "data-analysis": ["データ解析", "データマイニング", "位相的", "構造発見"],
            "machine-learning": ["機械学習", "深層学習", "AI", "ニューラル"],
            "programming": ["プログラミング", "Python", "アルゴリズム"]
        }
    
    def load_users_data(self):
        """既存のユーザーデータを読み込み"""
        try:
            with open(self.users_json_path, 'r', encoding='utf-8') as f:
                self.users_data = json.load(f)
        except FileNotFoundError:
            self.users_data = {"users": [], "categories": {}}
    
    def save_users_data(self):
        """ユーザーデータをJSONファイルに保存"""
        with open(self.users_json_path, 'w', encoding='utf-8') as f:
            json.dump(self.users_data, f, ensure_ascii=False, indent=2)
    
    def parse_tsv_file(self, tsv_path: str) -> pd.DataFrame:
        """TSVファイルを解析してDataFrameとして返す"""
        try:
            # TSVファイルを読み込み（タブ区切り、ヘッダーなし）
            df = pd.read_csv(tsv_path, sep='\t', header=None, encoding='utf-8')
            
            # 実際の列数を確認
            print(f"TSVファイルの列数: {len(df.columns)}")
            print(f"最初の行: {df.iloc[0].tolist()}")
            
            # 空の最後の列を削除（末尾のタブによる場合）
            if len(df.columns) == 8 and df.iloc[:, 7].isna().all():
                df = df.iloc[:, :7]
                print("空の8列目を削除しました")
            
            # 列名を設定
            if len(df.columns) == 7:
                df.columns = ['id', 'book_id', 'checkout_date', 'return_date', 'location', 'classification', 'title_author']
            else:
                print(f"予期しない列数: {len(df.columns)}")
                return pd.DataFrame()
            
            return df
        except Exception as e:
            print(f"TSVファイルの読み込みエラー: {e}")
            return pd.DataFrame()
    
    def extract_book_info(self, title_author: str) -> Tuple[str, str]:
        """タイトルと著者を分離"""
        # " / " で分割して最初の部分をタイトル、残りを著者とする
        parts = title_author.split(' / ')
        title = parts[0].strip()
        author = parts[1].strip() if len(parts) > 1 else "不明"
        
        # タイトルから余分な情報を除去
        title = re.sub(r'\s*;.*$', '', title)  # セミコロン以降を除去
        
        return title, author
    
    def categorize_book(self, title: str, author: str) -> str:
        """書籍をカテゴリに分類"""
        text = f"{title} {author}".lower()
        
        # 各カテゴリのキーワードをチェック
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return category
        
        return "other"  # デフォルトカテゴリ
    
    def generate_cover_url(self, title: str, author: str) -> str:
        """書籍カバー画像のURLを生成（プレースホルダー）"""
        # 実際の実装では、Amazon API や Google Books API を使用
        # ここではプレースホルダー画像を返す
        return "https://via.placeholder.com/240x360/f0f0f0/666?text=Book+Cover"
    
    def analyze_reading_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """読書パターンを分析"""
        if df.empty:
            return {}
        
        # 日付を datetime に変換
        df['checkout_date'] = pd.to_datetime(df['checkout_date'])
        df['return_date'] = pd.to_datetime(df['return_date'])
        
        # 年月別の統計
        df['year'] = df['checkout_date'].dt.year
        df['month'] = df['checkout_date'].dt.month
        
        # 今年と全体の統計
        current_year = datetime.now().year
        this_year_count = len(df[df['year'] == current_year])
        total_count = len(df)
        
        # 月別統計（今年）
        monthly_stats = df[df['year'] == current_year].groupby('month').size().to_dict()
        
        # ユニークな書籍の抽出
        unique_books = df.drop_duplicates(subset=['book_id'])
        
        return {
            'total_books': len(unique_books),
            'this_year_books': this_year_count,
            'monthly_stats': monthly_stats,
            'unique_books': unique_books
        }
    
    def create_user_profile(self, user_id: str, name: str, position: str, 
                          avatar: str, df: pd.DataFrame) -> Dict[str, Any]:
        """ユーザープロファイルを作成"""
        
        analysis = self.analyze_reading_patterns(df)
        if not analysis:
            return None
        
        unique_books = analysis['unique_books']
        
        # 読書履歴の生成
        reading_history = []
        category_counts = Counter()
        
        for _, row in unique_books.iterrows():
            title, author = self.extract_book_info(row['title_author'])
            category = self.categorize_book(title, author)
            year = str(row['checkout_date'].year)
            
            book_entry = {
                "title": title,
                "author": author,
                "category": category,
                "year": year,
                "rating": 4,  # デフォルト評価
                "cover": self.generate_cover_url(title, author)
            }
            reading_history.append(book_entry)
            category_counts[category] += 1
        
        # 専門分野の特定（上位カテゴリ）
        top_categories = [cat for cat, _ in category_counts.most_common(4)]
        specializations = []
        for cat in top_categories:
            if cat in self.users_data.get('categories', {}):
                specializations.append(self.users_data['categories'][cat]['name'])
        
        # 現在読んでいる本（最新の本）
        current_reading = reading_history[0] if reading_history else None
        if current_reading:
            current_reading['progress'] = 0.7  # デフォルト進行度
        
        # ユーザープロファイルの構築
        user_profile = {
            "id": user_id,
            "name": name,
            "nameJa": name,  # 日本語名は同じに設定
            "position": position,
            "avatar": avatar,
            "email": f"{user_id}@example.com",
            "specializations": specializations,
            "stats": {
                "totalBooks": analysis['total_books'],
                "thisYearBooks": analysis['this_year_books'],
                "publications": 0,  # 学生の場合は0
                "presentations": 1 if analysis['total_books'] > 10 else 0,
                "datasets": 0,
                "coderepos": 1 if analysis['total_books'] > 5 else 0,
                "awards": 0
            },
            "currentReading": current_reading,
            "readingHistory": reading_history,
            "networkConnections": []  # 後で設定
        }
        
        return user_profile
    
    def generate_mypage_html(self, user_profile: Dict[str, Any]) -> str:
        """ユーザープロファイルからマイページHTMLを生成"""
        
        # 専門分野の統計計算
        category_stats = Counter()
        for book in user_profile['readingHistory']:
            category_stats[book['category']] += 1
        
        total_books = len(user_profile['readingHistory'])
        category_percentages = {}
        for cat, count in category_stats.items():
            category_percentages[cat] = round((count / total_books) * 100)
        
        # 月別統計の生成（ダミーデータ）
        monthly_bars = []
        for i in range(6):
            height = min(100, max(20, (i + 1) * 20))
            count = max(1, height // 20)
            monthly_bars.append(f'<div class="bar" style="height: {height}%;" data-value="{count}冊"></div>')
        
        # 専門分野のドーナツチャートとレジェンド
        donut_colors = []
        legend_items = []
        total_percent = 0
        
        for i, (cat, percentage) in enumerate(category_percentages.items()):
            if cat in self.users_data.get('categories', {}):
                cat_info = self.users_data['categories'][cat]
                color = cat_info['color']
                name = cat_info['name']
                
                donut_colors.append(f"{color} {total_percent}% {total_percent + percentage}%")
                legend_items.append(f'<li><span class="legend-color-box" style="background-color: {color};"></span> {name} ({percentage}%)</li>')
                total_percent += percentage
                
                if len(donut_colors) >= 4:  # 最大4つまで
                    break
        
        donut_gradient = f"conic-gradient({', '.join(donut_colors)})"
        legend_html = '\n                            '.join(legend_items)
        
        # 書籍カードの生成
        book_cards = []
        for book in user_profile['readingHistory'][:9]:  # 最大9冊表示
            stars = "★" * book['rating'] + "☆" * (5 - book['rating'])
            book_cards.append(f'''
                            <div class="book-card" data-category="{book['category']}" data-year="{book['year']}">
                                <img src="{book['cover']}" alt="Book Cover" class="cover">
                                <div class="book-info">
                                    <h4>{book['title']}</h4>
                                    <p>{book['author']}</p>
                                    <div class="rating">{stars}</div>
                                </div>
                            </div>''')
        
        # HTMLテンプレートの生成
        html_content = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>マイライブラリ - {user_profile['name']}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@0.378.0/dist/umd/lucide.min.js"></script>
    <style>
        /* CSS styles from mypage_amane.html would go here */
        /* [CSS content truncated for brevity] */
    </style>
</head>
<body>
    <div class="user-header">
        <div class="user-selector">
            <label for="user-select">ユーザー:</label>
            <select id="user-select" class="user-dropdown" onchange="switchUser()">
                <option value="{user_profile['id']}" selected>{user_profile['name']}</option>
                <option value="yohei">Yohei Sawada (准教授)</option>
                <option value="default">デフォルトユーザー</option>
            </select>
            <img id="user-avatar" src="{user_profile['avatar']}" alt="User Avatar" class="user-avatar">
        </div>
    </div>

    <div class="dashboard-container">
        <header class="page-header">
            <h1 id="page-title">マイライブラリ</h1>
            <div class="mode-switcher">
                <button class="mode-btn active" id="general-mode-btn">
                    <i data-lucide="library"></i>
                    <span>一般モード</span>
                </button>
                <button class="mode-btn" id="research-mode-btn">
                    <i data-lucide="flask-conical"></i>
                    <span>研究モード</span>
                </button>
                <button class="mode-btn" id="network-mode-btn" onclick="location.href='network_graph.html'">
                    <i data-lucide="network"></i>
                    <span>ネットワーク</span>
                </button>
            </div>
        </header>

        <header class="profile-header">
            <img src="{user_profile['avatar']}" alt="User Avatar" class="avatar">
            <div class="user-info">
                <h2>{user_profile['name']}</h2>
                <p>{user_profile['position']}</p>
            </div>
            <div class="profile-stats">
                <div class="stat-item"><div class="number">{user_profile['stats']['totalBooks']}</div><div class="label">総文献数</div></div>
                <div class="stat-item"><div class="number">{user_profile['stats']['thisYearBooks']}</div><div class="label">今年の文献数</div></div>
            </div>
        </header>

        <div id="view-wrapper">
            <div id="general-view">
                <aside class="stats-sidebar">
                    <div class="stats-widget">
                        <h3>月間読書グラフ (2025年)</h3>
                        <div class="bar-chart">
                            {''.join(monthly_bars)}
                        </div>
                    </div>
                    <div class="stats-widget">
                        <h3>専門分野</h3>
                        <div class="donut-chart" style="background: {donut_gradient};"></div>
                        <ul class="legend-list">
                            {legend_html}
                        </ul>
                    </div>
                </aside>
                <main class="main-library">
                    <section class="section-card currently-reading">
                        <h2>今読んでいる文献</h2>
                        <div class="progress-book">
                            <img src="{user_profile['currentReading']['cover'] if user_profile['currentReading'] else ''}" alt="Book cover">
                            <div class="progress-details">
                                <h4>{user_profile['currentReading']['title'] if user_profile['currentReading'] else ''}</h4>
                                <p>{user_profile['currentReading']['author'] if user_profile['currentReading'] else ''}</p>
                                <div class="progress-bar-bg"><div class="progress-bar-fg" style="width: {int(user_profile['currentReading']['progress'] * 100) if user_profile['currentReading'] else 0}%;"></div></div>
                            </div>
                        </div>
                    </section>
                    <section class="bookshelf">
                        <div class="bookshelf-grid">
                            {''.join(book_cards)}
                        </div>
                    </section>
                </main>
            </div>
        </div>
    </div>

    <script src="js/user_manager.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            lucide.createIcons();
        }});
    </script>
</body>
</html>'''
        
        return html_content
    
    def add_user_to_database(self, user_profile: Dict[str, Any]):
        """ユーザープロファイルをデータベースに追加"""
        # 既存ユーザーをチェック
        existing_users = [u['id'] for u in self.users_data['users']]
        
        if user_profile['id'] not in existing_users:
            self.users_data['users'].append(user_profile)
            print(f"新しいユーザー '{user_profile['name']}' を追加しました。")
        else:
            # 既存ユーザーの更新
            for i, user in enumerate(self.users_data['users']):
                if user['id'] == user_profile['id']:
                    self.users_data['users'][i] = user_profile
                    print(f"ユーザー '{user_profile['name']}' を更新しました。")
                    break
        
        # ネットワークセクションを追加/更新
        self.update_network_data(user_profile)
    
    def update_network_data(self, user_profile: Dict[str, Any]):
        """ネットワークデータを更新"""
        # networkセクションが存在しない場合は作成
        if 'network' not in self.users_data:
            self.users_data['network'] = {
                'nodes': [],
                'edges': []
            }
        
        # ノードを追加/更新
        existing_node_ids = [node['id'] for node in self.users_data['network']['nodes']]
        
        new_node = {
            'id': user_profile['id'],
            'label': user_profile['name'],
            'name': user_profile['name'],
            'avatar': user_profile['avatar'],
            'group': 'student',  # デフォルトグループ
            'field': ', '.join(user_profile['specializations'][:2]) if user_profile['specializations'] else 'その他'
        }
        
        if user_profile['id'] not in existing_node_ids:
            self.users_data['network']['nodes'].append(new_node)
            print(f"ネットワークノード '{user_profile['name']}' を追加しました。")
        else:
            # 既存ノードを更新
            for i, node in enumerate(self.users_data['network']['nodes']):
                if node['id'] == user_profile['id']:
                    self.users_data['network']['nodes'][i] = new_node
                    print(f"ネットワークノード '{user_profile['name']}' を更新しました。")
                    break
        
        # 基本的な接続を作成（他のユーザーとの関連性に基づく）
        self.create_user_connections(user_profile)
    
    def create_user_connections(self, user_profile: Dict[str, Any]):
        """ユーザー間の接続を作成（専門分野の共通性に基づく）"""
        user_specializations = set(user_profile['specializations'])
        
        # 既存のエッジIDを取得
        existing_edges = [(edge['from'], edge['to']) for edge in self.users_data['network']['edges']]
        
        # 他のユーザーとの関連性をチェック
        for other_user in self.users_data['users']:
            if other_user['id'] == user_profile['id']:
                continue
            
            other_specializations = set(other_user.get('specializations', []))
            
            # 共通の専門分野があるかチェック
            common_fields = user_specializations.intersection(other_specializations)
            
            if common_fields and len(common_fields) > 0:
                # 接続を作成
                edge_tuple = (user_profile['id'], other_user['id'])
                reverse_edge_tuple = (other_user['id'], user_profile['id'])
                
                if edge_tuple not in existing_edges and reverse_edge_tuple not in existing_edges:
                    new_edge = {
                        'from': user_profile['id'],
                        'to': other_user['id'],
                        'label': f"共通分野: {', '.join(list(common_fields)[:2])}",
                        'strength': len(common_fields)
                    }
                    self.users_data['network']['edges'].append(new_edge)
                    print(f"接続を作成: {user_profile['name']} -> {other_user['name']} ({', '.join(common_fields)})")
    
    def process_tsv_file(self, tsv_path: str, user_id: str, name: str, 
                        position: str, avatar: str = None) -> bool:
        """TSVファイルを処理してマイページを生成"""
        
        print(f"TSVファイルを処理中: {tsv_path}")
        
        # TSVファイルの解析
        df = self.parse_tsv_file(tsv_path)
        if df.empty:
            print("TSVファイルの読み込みに失敗しました。")
            return False
        
        # アバター画像のデフォルト設定
        if not avatar:
            avatar = f"https://via.placeholder.com/90x90/{user_id[0].upper()}/fff?text={user_id[0].upper()}"
        
        # ユーザープロファイルの作成
        user_profile = self.create_user_profile(user_id, name, position, avatar, df)
        if not user_profile:
            print("ユーザープロファイルの作成に失敗しました。")
            return False
        
        # データベースに追加
        self.add_user_to_database(user_profile)
        
        # マイページHTMLの生成
        html_content = self.generate_mypage_html(user_profile)
        
        # HTMLファイルの保存（相対パスを使用）
        src_folder = self.project_root / "src"
        src_folder.mkdir(exist_ok=True)  # srcフォルダが存在しない場合は作成
        html_filename = src_folder / f"mypage_{user_id}.html"
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # ユーザーデータの保存
        self.save_users_data()
        
        print(f"マイページを生成しました: {html_filename}")
        print(f"ユーザーデータを更新しました: {self.users_json_path}")
        
        return True


def main():
    parser = argparse.ArgumentParser(description='TSVファイルからマイページを自動生成')
    parser.add_argument('tsv_file', help='TSVファイルのパス')
    parser.add_argument('--user-id', required=True, help='ユーザーID')
    parser.add_argument('--name', required=True, help='ユーザー名')
    parser.add_argument('--position', required=True, help='所属・役職')
    parser.add_argument('--avatar', help='アバター画像のURL')
    parser.add_argument('--users-json', default='data/users.json', help='ユーザーデータJSONファイルのパス')
    
    args = parser.parse_args()
    
    # マイページ生成器の初期化
    generator = MypageGenerator(args.users_json)
    
    # TSVファイルの処理
    success = generator.process_tsv_file(
        args.tsv_file,
        args.user_id,
        args.name,
        args.position,
        args.avatar
    )
    
    if success:
        print("マイページの生成が完了しました。")
    else:
        print("マイページの生成に失敗しました。")


if __name__ == "__main__":
    main()
