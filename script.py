import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os
import numpy as np

# --- 設定項目 ---
# 1. 分析したいCSVファイルの名前を指定
CSV_FILE_NAME = 'your_survey_data.csv' 

# 2. 生成されるPDFファイルの名前を指定
PDF_FILE_NAME = 'アンケート結果レポート.pdf'

# 3. 無視したい質問（列のヘッダー名）を指定 - index.htmlを参考に拡張
IGNORED_HEADERS_EXACT = ["学校名"]
IGNORED_HEADERS_CONTAIN = [
    "submission id", "submit date", "start date", "end date", 
    "ip address", "network id", "tags", "user agent",
    "fillout_account_id", "submission_edit_link", "timestamp",
    "status", "url", "error", "current step", "last updated", 
    "submission started"
]

# 4. グラフ化せず、自由記述として扱う選択肢の最大数
FREE_TEXT_THRESHOLD = 15

# 5. グラフ品質設定
DPI = 300  # 高解像度
FIGURE_SIZE = (10, 6)  # より大きなサイズ

# --- Matplotlibの高品質設定 ---
# 高解像度設定
plt.rcParams['figure.dpi'] = DPI
plt.rcParams['savefig.dpi'] = DPI
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['savefig.transparent'] = False
plt.rcParams['savefig.facecolor'] = 'white'

# スクリプトと同じ場所にあるフォントファイルを指定
font_path = os.path.join(os.path.dirname(__file__), 'ipaexg.ttf')
if os.path.exists(font_path):
    matplotlib.font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = 'IPAexGothic'
    plt.rcParams['font.size'] = 12
else:
    print(f"警告: フォントファイル '{font_path}' が見つかりません。日本語が正しく表示されない可能性があります。")
    plt.rcParams['font.family'] = 'sans-serif'

# モダンなカラーパレット（index.htmlから）
CHART_COLORS = [
    '#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#3B82F6',
    '#D946EF', '#6EE7B7', '#FCD34D', '#6366F1', '#F472B6'
]

class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        if os.path.exists(font_path):
            self.add_font('IPAexGothic', '', font_path)
            self.set_font('IPAexGothic', '', 18)
        else:
            self.set_font('Arial', 'B', 18)
        
        # グラデーション風のヘッダー背景（より深い色）
        self.set_fill_color(99, 102, 241)  # インディゴ色
        self.set_draw_color(67, 56, 202)  # より濃い境界線
        self.set_line_width(1.0)
        self.rect(0, 0, self.w, 28, 'FD')
        
        # 白いテキスト（太字で大きく）
        self.set_text_color(255, 255, 255)
        self.cell(0, 22, 'アンケート結果レポート ✨', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        # テキスト色を黒に戻す
        self.set_text_color(0, 0, 0)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        if os.path.exists(font_path):
            self.set_font('IPAexGothic', '', 10)
        else:
            self.set_font('Arial', '', 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
    def check_page_break(self, height):
        """指定した高さの要素を追加する前に、改ページが必要かチェックする"""
        # より保守的な判定：ページ下部に近い場合は早めに改ページ
        safe_margin = 20  # 下部20mmは安全マージン
        if self.get_y() + height > (self.page_break_trigger - safe_margin):
            self.add_page()
            
    def add_question_title(self, title, is_chart=True):
        """質問文のタイトルを追加する"""
        # グラフの場合はタイトル+グラフの高さ、自由記述の場合はタイトル+最低限の高さで判定
        required_height = 150 if is_chart else 50
        self.check_page_break(required_height)
        
        # アイコン付きのタイトル
        icon = "📊" if is_chart else "📝"
        title_text = f'{icon} Q. {title}'
        
        # フォント設定（太字で見やすく）
        if os.path.exists(font_path):
            self.set_font('IPAexGothic', '', 14)
        else:
            self.set_font('Arial', 'B', 14)
        
        # タイトルの必要な高さを動的に計算
        # 文字列の長さに基づいて行数を推定
        chars_per_line = 45  # A4幅での1行あたりの文字数（概算）
        estimated_lines = max(1, (len(title_text) // chars_per_line) + 1)
        title_height = max(12, estimated_lines * 7 + 6)  # 最低12mm、行数に応じて調整
        
        # より鮮明な色設定
        if is_chart:
            self.set_fill_color(139, 92, 246)  # 紫色（グラフ用）
            self.set_text_color(255, 255, 255)  # 白文字
        else:
            self.set_fill_color(59, 130, 246)  # 青色（自由記述用）
            self.set_text_color(255, 255, 255)  # 白文字
        
        self.set_draw_color(75, 85, 99)  # ダークグレーの境界線
        self.set_line_width(0.5)  # 境界線を少し太く
        
        # タイトルボックスを描画
        box_x = 10
        box_y = self.get_y()
        box_width = self.w - 20
        
        self.rect(box_x, box_y, box_width, title_height, 'FD')
        
        # テキストを中央に配置
        self.set_xy(box_x + 5, box_y + 3)
        
        # multi_cellの幅をボックス内に収める
        text_width = box_width - 10
        self.multi_cell(text_width, 6, title_text, 0, align='L')
        
        # テキスト色を黒に戻す
        self.set_text_color(0, 0, 0)
        
        # ボックスの下に移動
        self.set_y(box_y + title_height + 5)
        self.ln(3)

def should_ignore_column(header):
    """列を無視すべきかどうかを判定"""
    if not header or pd.isna(header):
        return True
        
    header_lower = str(header).lower().strip()
    
    # 完全一致チェック
    if any(ignored.lower() == header_lower for ignored in IGNORED_HEADERS_EXACT):
        return True
        
    # 部分一致チェック
    if any(term in header_lower for term in IGNORED_HEADERS_CONTAIN):
        return True
        
    return False

def create_modern_chart(counts, title, total_responses):
    """モダンなデザインのグラフを作成"""
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    
    # 背景を白に設定
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # データ準備
    labels = list(counts.index)
    values = list(counts.values)
    
    # カラーパレットを適用
    colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(labels))]
    
    # 円グラフの作成
    wedges, texts, autotexts = ax.pie(
        values, 
        labels=labels, 
        autopct=lambda pct: f'{pct:.1f}%' if pct > 3 else '',
        startangle=90,
        colors=colors,
        textprops={'fontsize': 11, 'weight': 'bold'},
        pctdistance=0.85
    )
    
    # パーセンテージのテキストを白に
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    # タイトル（より見やすく）
    ax.set_title(f'回答数: {total_responses}件', 
                fontsize=13, fontweight='bold', pad=15,
                color='#1F2937')  # より濃いグレー
    
    # 凡例の改善
    ax.legend(wedges, [f'{label}: {value}件' for label, value in zip(labels, values)],
             title="回答内訳",
             loc="center left",
             bbox_to_anchor=(1, 0, 0.5, 1),
             fontsize=10)
    
    plt.tight_layout()
    return fig

def create_report():
    # 1. CSV読み込み
    try:
        df = pd.read_csv(CSV_FILE_NAME, encoding='utf-8')
        print(f"📁 CSVファイルを読み込みました: {CSV_FILE_NAME}")
        print(f"   データ行数: {len(df)}, 列数: {len(df.columns)}")
    except FileNotFoundError:
        print(f"❌ エラー: CSVファイル '{CSV_FILE_NAME}' が見つかりません。")
        return
    except Exception as e:
        print(f"❌ エラー: CSVファイルの読み込み中に問題が発生しました。 {e}")
        return

    # 2. PDFの準備
    pdf = PDF()
    pdf.add_page()

    # 一時的な画像保存用ディレクトリ
    charts_dir = 'charts'
    if not os.path.exists(charts_dir):
        os.makedirs(charts_dir)

    processed_questions = 0
    
    # 3. 各質問をループ処理
    for header in df.columns:
        # 無視すべき列かチェック
        if should_ignore_column(header):
            print(f"⏭️  スキップ: {header}")
            continue
        
        # 回答データ（空白を除外）
        answers = df[header].dropna()
        answers = answers[answers.astype(str).str.strip() != '']
        
        if answers.empty:
            print(f"⚠️  データなし: {header}")
            continue
            
        counts = answers.value_counts()
        total_responses = len(answers)
        unique_responses = len(counts)
        
        print(f"📊 処理中: {header}")
        print(f"   回答数: {total_responses}, ユニーク数: {unique_responses}")
        
        # 4. グラフ化するか自由記述にするか判定（index.htmlのロジックを参考）
        is_likely_free_text = (
            unique_responses > (total_responses * 0.6) or 
            unique_responses > FREE_TEXT_THRESHOLD or 
            total_responses < 5
        )
        is_chartable = (
            not is_likely_free_text and 
            unique_responses >= 2 and 
            unique_responses <= 20 and 
            total_responses >= unique_responses
        )
        
        pdf.add_question_title(header, is_chartable)
        
        if is_chartable:
            # 高品質グラフを作成
            fig = create_modern_chart(counts, header, total_responses)
            
            # 安全なファイル名を生成
            safe_filename = "".join(c for c in header if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_filename = safe_filename.replace(' ', '_')[:50]  # 長すぎる場合は切り詰め
            chart_path = os.path.join(charts_dir, f'chart_{processed_questions}_{safe_filename}.png')
            
            # 高解像度で保存
            fig.savefig(chart_path, dpi=DPI, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            # PDFに画像を挿入（既にタイトルで改ページ判定済みなので、ここでは追加チェック不要）
            pdf.image(chart_path, x=15, w=180)
            pdf.ln(10)

        else:
            # 自由記述として一覧表示（デザイン改善）
            if os.path.exists(font_path):
                pdf.set_font('IPAexGothic', '', 10)
            else:
                pdf.set_font('Arial', '', 10)
                
            # 背景色付きで表示
            pdf.set_fill_color(249, 250, 251)  # 薄いグレー背景
            
            # 自由記述のリストを表示する前に、最初の数項目が確実に同じページに収まるかチェック
            unique_answers = answers.unique()[:50]
            
            for i, ans in enumerate(unique_answers):  # 最大50件まで表示
                # 文字数制限
                display_text = str(ans)[:100] + ('...' if len(str(ans)) > 100 else '')
                
                # 項目の必要な高さを計算（テキストの長さに応じて）
                text_lines = len(display_text) // 80 + 1  # 1行約80文字として計算
                item_height = max(10, text_lines * 6 + 4)  # 最低10mm、テキスト行数に応じて調整
                
                # 項目全体がページに収まるかチェック
                pdf.check_page_break(item_height)
                
                # 交互に背景色を変える（より明確なコントラスト）
                if i % 2 == 0:
                    pdf.set_fill_color(243, 244, 246)  # 薄いグレー
                    pdf.set_draw_color(229, 231, 235)  # 境界線
                else:
                    pdf.set_fill_color(255, 255, 255)  # 白
                    pdf.set_draw_color(229, 231, 235)  # 境界線
                
                # テキストボックス風に表示（境界線付き）
                current_y = pdf.get_y()
                pdf.set_line_width(0.2)
                pdf.rect(15, current_y, 180, item_height - 2, 'FD')
                
                # テキストの位置を調整
                pdf.set_xy(20, current_y + 2)
                
                # フォントサイズを少し調整
                if os.path.exists(font_path):
                    pdf.set_font('IPAexGothic', '', 10)
                else:
                    pdf.set_font('Arial', '', 10)
                
                pdf.multi_cell(170, 5, f'• {display_text}', 0, align='L')
                pdf.ln(2)
            
            if len(answers.unique()) > 50:
                pdf.set_text_color(128, 128, 128)
                pdf.cell(0, 8, f'... 他 {len(answers.unique()) - 50} 件', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
                pdf.set_text_color(0, 0, 0)
            
            pdf.ln(5)
        
        processed_questions += 1

    # 5. PDFを保存
    try:
        pdf.output(PDF_FILE_NAME)
        print(f"🎉 レポートが完成しました！")
        print(f"   ファイル名: {PDF_FILE_NAME}")
        print(f"   処理した質問数: {processed_questions}")
    except Exception as e:
        print(f"❌ エラー: PDFの保存中に問題が発生しました。 {e}")
        
    # 一時ファイルをクリーンアップ
    try:
        for file in os.listdir(charts_dir):
            os.remove(os.path.join(charts_dir, file))
        os.rmdir(charts_dir)
        print("🧹 一時ファイルをクリーンアップしました。")
    except Exception as e:
        print(f"⚠️  クリーンアップ中に警告: {e}")

# --- スクリプト実行 ---
if __name__ == '__main__':
    print("🚀 アンケート結果レポート生成開始")
    create_report()
    print("✅ 処理完了")