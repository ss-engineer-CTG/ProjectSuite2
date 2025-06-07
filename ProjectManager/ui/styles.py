"""
UIスタイル定義
"""

class Colors:
    """カラー定義"""
    BACKGROUND = '#1A1A1A'
    CARD_BG = '#2D2D2D'
    BUTTON_PRIMARY = '#E0E0E0'
    BUTTON_DANGER = '#FF3B30'
    BUTTON_INFO = '#4A90E2'
    TEXT_PRIMARY = '#FFFFFF'
    TEXT_SECONDARY = '#B0B0B0'
    BUTTON_HOVER = '#F5F5F5'
    BUTTON_TEXT = '#1A1A1A'
    INPUT_BG = '#3D3D3D'
    INPUT_TEXT = '#FFFFFF'
    INPUT_BORDER = '#505050'
    FRAME_BORDER = '#404040'
    
    # ステータスカラー
    STATUS_COLORS = {
        '進行中': '#E0E0E0',
        '完了': '#CCCCCC',
        '中止': '#999999'
    }
    
    @classmethod
    def get_status_color(cls, status: str) -> str:
        return cls.STATUS_COLORS.get(status, cls.TEXT_SECONDARY)

class Fonts:
    """フォント定義"""
    DEFAULT = ("Meiryo", 12)
    HEADER = ("Meiryo", 14, "bold")
    TITLE = ("Meiryo", 20, "bold")
    SMALL = ("Meiryo", 10)
    BUTTON = ("Meiryo", 12)

class Sizes:
    """サイズ定義"""
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600
    PADDING_SMALL = 5
    PADDING_MEDIUM = 10
    PADDING_LARGE = 20
    BUTTON_WIDTH_SMALL = 80
    BUTTON_WIDTH_MEDIUM = 100
    BUTTON_WIDTH_LARGE = 150
    ENTRY_WIDTH = 250
    LABEL_WIDTH = 120