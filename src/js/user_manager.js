/**
 * User Manager - ユーザー情報の管理とページ間での統一的なユーザー切り替え機能
 */

class UserManager {
    constructor() {
        this.users = [];
        this.currentUser = null;
        this.categories = {};
        this.initialized = false;
    }

    /**
     * ユーザーデータを初期化
     */
    async init() {
        try {
            const response = await fetch('data/users.json');
            const data = await response.json();
            this.users = data.users;
            this.categories = data.categories;
            this.initialized = true;
            
            // 現在のユーザーを設定
            this.setCurrentUserFromPage();
            
            console.log('User Manager initialized with', this.users.length, 'users');
        } catch (error) {
            console.error('Failed to load user data:', error);
            // フォールバック: デフォルトユーザーのみ
            this.users = [
                {
                    id: 'default',
                    name: 'デフォルトユーザー',
                    position: '図書館利用者',
                    avatar: 'https://via.placeholder.com/90x90/ccc/666?text=User'
                }
            ];
            this.initialized = true;
        }
    }

    /**
     * 現在のページから適切なユーザーを設定
     */
    setCurrentUserFromPage() {
        const path = window.location.pathname;
        const filename = path.split('/').pop();
        
        if (filename === 'mypage.html') {
            this.currentUser = this.getUserById('yohei');
        } else if (filename.startsWith('mypage_')) {
            const userId = filename.replace('mypage_', '').replace('.html', '');
            this.currentUser = this.getUserById(userId);
        } else {
            this.currentUser = this.getUserById('default');
        }
    }

    /**
     * IDでユーザーを取得
     */
    getUserById(id) {
        return this.users.find(user => user.id === id) || this.users[0];
    }

    /**
     * すべてのユーザーを取得
     */
    getAllUsers() {
        return this.users;
    }

    /**
     * 現在のユーザーを取得
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * ユーザーを切り替え
     */
    switchUser(userId) {
        const user = this.getUserById(userId);
        if (!user) {
            console.error('User not found:', userId);
            return;
        }

        this.currentUser = user;
        
        // アバター画像を更新
        const avatarElement = document.getElementById('user-avatar');
        if (avatarElement) {
            avatarElement.src = user.avatar;
        }

        // 適切なページにリダイレクト
        this.redirectToUserPage(userId);
    }

    /**
     * ユーザーに応じたページにリダイレクト
     */
    redirectToUserPage(userId) {
        const currentPath = window.location.pathname;
        const currentFile = currentPath.split('/').pop();
        
        // マイページの場合は適切なマイページにリダイレクト
        if (currentFile.startsWith('mypage')) {
            if (userId === 'yohei') {
                window.location.href = 'mypage.html';
            } else if (userId === 'default') {
                window.location.href = 'my_library.html';
            } else {
                window.location.href = `mypage_${userId}.html`;
            }
        }
        // 他のページの場合は現在のページに留まる
    }

    /**
     * ユーザー選択ドロップダウンを初期化
     */
    initUserSelector() {
        const userSelect = document.getElementById('user-select');
        if (!userSelect) return;

        // 既存のオプションをクリア
        userSelect.innerHTML = '';

        // デフォルトユーザーを追加
        const defaultOption = document.createElement('option');
        defaultOption.value = 'default';
        defaultOption.textContent = 'デフォルトユーザー';
        userSelect.appendChild(defaultOption);

        // 登録済みユーザーを追加
        this.users.forEach(user => {
            if (user.id !== 'default') {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = `${user.name} (${user.position.split(' ').pop()})`;
                userSelect.appendChild(option);
            }
        });

        // 現在のユーザーを選択
        if (this.currentUser) {
            userSelect.value = this.currentUser.id;
        }

        // イベントリスナーを設定
        userSelect.addEventListener('change', (e) => {
            this.switchUser(e.target.value);
        });

        // アバター画像を初期化
        this.updateAvatar();
    }

    /**
     * アバター画像を更新
     */
    updateAvatar() {
        const avatarElement = document.getElementById('user-avatar');
        if (avatarElement && this.currentUser) {
            avatarElement.src = this.currentUser.avatar;
        }
    }

    /**
     * ネットワークグラフ用のノードデータを生成
     */
    generateNetworkNodes() {
        const nodes = [];
        const edges = [];

        this.users.forEach((user, index) => {
            if (user.id === 'default') return;

            // ノードを追加
            nodes.push({
                id: index + 1,
                label: user.name,
                title: `${user.name}\\n${user.position}`,
                image: user.avatar,
                shape: 'circularImage',
                size: user.id === 'yohei' ? 30 : 25, // 教授は少し大きく
                borderWidth: 2,
                borderColor: user.id === 'yohei' ? '#0074D9' : '#2ECC40',
                userId: user.id
            });

            // エッジを追加（ネットワーク接続）
            if (user.networkConnections) {
                user.networkConnections.forEach(connectionId => {
                    const connectedUser = this.getUserById(connectionId);
                    if (connectedUser) {
                        const connectedIndex = this.users.findIndex(u => u.id === connectionId);
                        if (connectedIndex !== -1) {
                            edges.push({
                                from: index + 1,
                                to: connectedIndex + 1,
                                color: { color: '#848484', highlight: '#0074D9' },
                                width: 2
                            });
                        }
                    }
                });
            }
        });

        return { nodes, edges };
    }

    /**
     * カテゴリ情報を取得
     */
    getCategory(categoryId) {
        return this.categories[categoryId] || {
            name: categoryId,
            color: '#cccccc',
            description: 'Unknown category'
        };
    }

    /**
     * ユーザーをデータベースに追加
     */
    addUser(userProfile) {
        const existingIndex = this.users.findIndex(u => u.id === userProfile.id);
        
        if (existingIndex !== -1) {
            // 既存ユーザーを更新
            this.users[existingIndex] = userProfile;
        } else {
            // 新しいユーザーを追加
            this.users.push(userProfile);
        }

        // UIを更新
        this.initUserSelector();
        
        console.log(`User ${userProfile.name} added/updated`);
    }

    /**
     * ユーザーデータをサーバーに保存（実際の実装では必要）
     */
    async saveUsersData() {
        try {
            const data = {
                users: this.users,
                categories: this.categories
            };
            
            // 実際の実装では API エンドポイントに POST
            console.log('Saving users data:', data);
            
            // ローカルストレージにも保存（開発用）
            localStorage.setItem('library_users', JSON.stringify(data));
        } catch (error) {
            console.error('Failed to save users data:', error);
        }
    }
}

// グローバルなユーザーマネージャーインスタンス
window.userManager = new UserManager();

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', async () => {
    await window.userManager.init();
    window.userManager.initUserSelector();
});

// レガシー関数（既存のHTMLファイルとの互換性のため）
function switchUser() {
    const userSelect = document.getElementById('user-select');
    if (userSelect && window.userManager) {
        window.userManager.switchUser(userSelect.value);
    }
}
