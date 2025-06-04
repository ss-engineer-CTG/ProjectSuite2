"""
UI スタイルとカラースキームの統一管理
KISS原則: シンプルなスタイル定義
DRY原則: 共通スタイルの統合
"""

class ColorScheme:
    """アプリケーション統一カラースキーム"""
    
    # 基本カラー
    BACKGROUND = '#1A1A1A'
    CARD_BG = '#2D2D2D'
    BUTTON_PRIMARY = '#E0E0E0'
    BUTTON_DANGER = '#FF3B30'
    TEXT_PRIMARY = '#FFFFFF'
    TEXT_SECONDARY = '#B0B0B0'
    BUTTON_HOVER = '#F5F5F5'
    BUTTON_TEXT = '#1A1A1A'
    
    # ステータスカラー
    STATUS_COLORS = {
        '進行中': '#E0E0E0',
        '完了': '#CCCCCC',
        '中止': '#999999'
    }
    
    # 入力フィールド
    INPUT_BG = '#3D3D3D'
    INPUT_TEXT = '#FFFFFF'
    INPUT_BORDER = '#505050'
    INPUT_PLACEHOLDER = '#808080'
    
    # フレーム・ボーダー
    FRAME_BORDER = '#404040'
    SEPARATOR = '#404040'
    
    # メッセージカラー
    ERROR = '#FF3B30'
    SUCCESS = '#28A745'
    WARNING = '#FFCC00'
    INFO = '#4A90E2'
    
    # スクロールバー
    SCROLLBAR_BG = '#2D2D2D'
    SCROLLBAR_FG = '#505050'
    
    @classmethod
    def get_status_color(cls, status: str) -> str:
        """ステータスに応じた色を取得"""
        return cls.STATUS_COLORS.get(status, cls.TEXT_SECONDARY)
    
    @classmethod
    def get_hover_color(cls, base_color: str) -> str:
        """ホバー色を取得"""
        return cls.BUTTON_HOVER
    
    @classmethod
    def get_pressed_color(cls, base_color: str) -> str:
        """押下時の色を取得"""
        return '#D0D0D0'

class FontScheme:
    """フォント設定の統一管理"""
    
    # 基本フォント
    DEFAULT_FONT = ("Meiryo", 12)
    HEADER_FONT = ("Meiryo", 14, "bold")
    TITLE_FONT = ("Meiryo", 20, "bold")
    SMALL_FONT = ("Meiryo", 10)
    
    # UI要素別フォント
    BUTTON_FONT = DEFAULT_FONT
    LABEL_FONT = DEFAULT_FONT
    ENTRY_FONT = DEFAULT_FONT
    
    @classmethod
    def get_font(cls, font_type: str = 'default'):
        """フォントタイプに応じたフォントを取得"""
        font_map = {
            'default': cls.DEFAULT_FONT,
            'header': cls.HEADER_FONT,
            'title': cls.TITLE_FONT,
            'small': cls.SMALL_FONT,
            'button': cls.BUTTON_FONT,
            'label': cls.LABEL_FONT,
            'entry': cls.ENTRY_FONT,
        }
        return font_map.get(font_type, cls.DEFAULT_FONT)

class UIConstants:
    """UI 定数の統一管理"""
    
    # ウィンドウサイズ
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600
    
    # パディング・マージン
    PADDING_SMALL = 5
    PADDING_MEDIUM = 10
    PADDING_LARGE = 20
    
    # ボタンサイズ
    BUTTON_WIDTH_SMALL = 80
    BUTTON_WIDTH_MEDIUM = 100
    BUTTON_WIDTH_LARGE = 150
    
    # 入力フィールドサイズ
    ENTRY_WIDTH_SMALL = 150
    ENTRY_WIDTH_MEDIUM = 250
    ENTRY_WIDTH_LARGE = 400
    
    # ラベル幅
    LABEL_WIDTH_STANDARD = 120
    LABEL_WIDTH_WIDE = 140
    
    @classmethod
    def get_window_geometry(cls, parent_window, width_ratio=0.8, height_ratio=0.8):
        """ウィンドウジオメトリの計算"""
        screen_width = parent_window.winfo_screenwidth()
        screen_height = parent_window.winfo_screenheight()
        
        window_width = max(int(screen_width * width_ratio), cls.MIN_WINDOW_WIDTH)
        window_height = max(int(screen_height * height_ratio), cls.MIN_WINDOW_HEIGHT)
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        return f"{window_width}x{window_height}+{x}+{y}"