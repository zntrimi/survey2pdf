import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os
import numpy as np
import tempfile
import zipfile
from io import BytesIO

# Streamlit configuration
st.set_page_config(
    page_title="Survey to PDF Report Generator",
    page_icon="📊",
    layout="wide"
)

# デフォルト設定
DEFAULT_IGNORED_HEADERS_EXACT = ["学校名"]
DEFAULT_IGNORED_HEADERS_CONTAIN = [
    "submission id", "submit date", "start date", "end date", 
    "ip address", "network id", "tags", "user agent",
    "fillout_account_id", "submission_edit_link", "timestamp",
    "status", "url", "error", "current step", "last updated", 
    "submission started"
]
DEFAULT_FREE_TEXT_THRESHOLD = 15
DEFAULT_DPI = 300
DEFAULT_FIGURE_SIZE = (10, 6)

# グラフ設定
plt.rcParams['figure.dpi'] = DEFAULT_DPI
plt.rcParams['savefig.dpi'] = DEFAULT_DPI
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['savefig.transparent'] = False
plt.rcParams['savefig.facecolor'] = 'white'

# フォント設定
font_path = os.path.join(os.path.dirname(__file__), 'ipaexg.ttf')
if os.path.exists(font_path):
    matplotlib.font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = 'IPAexGothic'
    plt.rcParams['font.size'] = 12
else:
    plt.rcParams['font.family'] = 'sans-serif'

# カラーパレット
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
        
        self.set_fill_color(99, 102, 241)
        self.set_draw_color(67, 56, 202)
        self.set_line_width(1.0)
        self.rect(0, 0, self.w, 28, 'FD')
        
        self.set_text_color(255, 255, 255)
        self.cell(0, 22, 'アンケート結果レポート ✨', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
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
        safe_margin = 20
        if self.get_y() + height > (self.page_break_trigger - safe_margin):
            self.add_page()
            
    def add_question_title(self, title, is_chart=True):
        required_height = 150 if is_chart else 50
        self.check_page_break(required_height)
        
        icon = "📊" if is_chart else "📝"
        title_text = f'{icon} Q. {title}'
        
        if os.path.exists(font_path):
            self.set_font('IPAexGothic', '', 14)
        else:
            self.set_font('Arial', 'B', 14)
        
        chars_per_line = 40
        estimated_lines = max(1, (len(title_text) // chars_per_line) + 1)
        title_height = max(15, estimated_lines * 8 + 8)
        
        if is_chart:
            self.set_fill_color(139, 92, 246)
            self.set_text_color(255, 255, 255)
        else:
            self.set_fill_color(59, 130, 246)
            self.set_text_color(255, 255, 255)
        
        self.set_draw_color(75, 85, 99)
        self.set_line_width(0.5)
        
        box_x = 10
        box_y = self.get_y()
        box_width = self.w - 20
        
        self.rect(box_x, box_y, box_width, title_height, 'FD')
        
        self.set_xy(box_x + 5, box_y + 4)
        
        text_width = box_width - 10
        self.multi_cell(text_width, 7, title_text, 0, align='L')
        
        self.set_text_color(0, 0, 0)
        
        self.set_y(box_y + title_height + 5)
        self.ln(3)

def should_ignore_column(header, ignored_exact, ignored_contain):
    if not header or pd.isna(header):
        return True
        
    header_lower = str(header).lower().strip()
    
    if any(ignored.lower() == header_lower for ignored in ignored_exact):
        return True
        
    if any(term in header_lower for term in ignored_contain):
        return True
        
    return False

def create_modern_chart(counts, title, total_responses):
    fig, ax = plt.subplots(figsize=DEFAULT_FIGURE_SIZE)
    
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    labels = list(counts.index)
    values = list(counts.values)
    
    colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(labels))]
    
    wedges, texts, autotexts = ax.pie(
        values, 
        labels=labels, 
        autopct=lambda pct: f'{pct:.1f}%' if pct > 3 else '',
        startangle=90,
        colors=colors,
        textprops={'fontsize': 11, 'weight': 'bold'},
        pctdistance=0.85
    )
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title(f'回答数: {total_responses}件', 
                fontsize=13, fontweight='bold', pad=15,
                color='#1F2937')
    
    ax.legend(wedges, [f'{label}: {value}件' for label, value in zip(labels, values)],
             title="回答内訳",
             loc="center left",
             bbox_to_anchor=(1, 0, 0.5, 1),
             fontsize=10)
    
    plt.tight_layout()
    return fig

def generate_report(df, ignored_exact, ignored_contain, free_text_threshold, max_display_answers, max_text_length, pdf_filename):
    pdf = PDF()
    pdf.add_page()

    with tempfile.TemporaryDirectory() as charts_dir:
        processed_questions = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_columns = len([col for col in df.columns if not should_ignore_column(col, ignored_exact, ignored_contain)])
        
        for i, header in enumerate(df.columns):
            if should_ignore_column(header, ignored_exact, ignored_contain):
                continue
            
            progress = (i + 1) / len(df.columns)
            progress_bar.progress(progress)
            status_text.text(f"処理中: {header}")
            
            answers = df[header].dropna()
            answers = answers[answers.astype(str).str.strip() != '']
            
            if answers.empty:
                continue
                
            counts = answers.value_counts()
            total_responses = len(answers)
            unique_responses = len(counts)
            
            is_likely_free_text = (
                unique_responses > (total_responses * 0.6) or 
                unique_responses > free_text_threshold or 
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
                fig = create_modern_chart(counts, header, total_responses)
                
                safe_filename = "".join(c for c in header if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_filename = safe_filename.replace(' ', '_')[:50]
                chart_path = os.path.join(charts_dir, f'chart_{processed_questions}_{safe_filename}.png')
                
                fig.savefig(chart_path, dpi=DEFAULT_DPI, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                plt.close(fig)
                
                pdf.image(chart_path, x=15, w=180)
                pdf.ln(10)

            else:
                if os.path.exists(font_path):
                    pdf.set_font('IPAexGothic', '', 10)
                else:
                    pdf.set_font('Arial', '', 10)
                    
                pdf.set_fill_color(249, 250, 251)
                
                # 表示制限を緩和（設定可能）
                unique_answers = answers.unique()[:max_display_answers]
                
                for j, ans in enumerate(unique_answers):
                    # 文字数制限を設定可能に
                    display_text = str(ans)[:max_text_length] + ('...' if len(str(ans)) > max_text_length else '')
                    
                    # より正確な行数計算
                    chars_per_line = 60
                    text_lines = max(1, (len(display_text) // chars_per_line) + 1)
                    item_height = max(12, text_lines * 6 + 6)
                    
                    pdf.check_page_break(item_height)
                    
                    if j % 2 == 0:
                        pdf.set_fill_color(243, 244, 246)
                        pdf.set_draw_color(229, 231, 235)
                    else:
                        pdf.set_fill_color(255, 255, 255)
                        pdf.set_draw_color(229, 231, 235)
                    
                    current_y = pdf.get_y()
                    pdf.set_line_width(0.2)
                    pdf.rect(15, current_y, 180, item_height, 'FD')
                    
                    pdf.set_xy(20, current_y + 3)
                    
                    if os.path.exists(font_path):
                        pdf.set_font('IPAexGothic', '', 10)
                    else:
                        pdf.set_font('Arial', '', 10)
                    
                    pdf.multi_cell(170, 5, f'• {display_text}', 0, align='L')
                    pdf.ln(2)
                
                # 制限を緩和した場合の表示
                if len(answers.unique()) > max_display_answers:
                    pdf.set_text_color(128, 128, 128)
                    pdf.cell(0, 8, f'... 他 {len(answers.unique()) - max_display_answers} 件', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
                    pdf.set_text_color(0, 0, 0)
                
                pdf.ln(5)
            
            processed_questions += 1

        progress_bar.progress(1.0)
        status_text.text("PDFを生成中...")
        
        # PDFをメモリに保存
        pdf_buffer = BytesIO()
        pdf_output = pdf.output(dest='S')
        pdf_buffer.write(pdf_output)
        pdf_buffer.seek(0)
        
        return pdf_buffer, processed_questions

def main():
    st.title("📊 Survey to PDF Report Generator")
    st.markdown("CSVファイルをアップロードして、アンケート結果のPDFレポートを生成します。")
    
    # サイドバーで設定
    st.sidebar.header("⚙️ 設定")
    
    # ファイルアップロード
    uploaded_file = st.file_uploader("CSVファイルを選択", type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
            st.success(f"✅ CSVファイルを読み込みました (行数: {len(df)}, 列数: {len(df.columns)})")
            
            # プレビュー表示
            with st.expander("📋 データプレビュー"):
                st.dataframe(df.head())
            
            # 設定項目
            st.sidebar.subheader("🚫 無視する列の設定")
            
            # 完全一致で無視する列
            ignored_exact_text = st.sidebar.text_area(
                "完全一致で無視する列名（1行に1つ）",
                value="\n".join(DEFAULT_IGNORED_HEADERS_EXACT),
                height=100
            )
            ignored_exact = [line.strip() for line in ignored_exact_text.split('\n') if line.strip()]
            
            # 部分一致で無視する列
            ignored_contain_text = st.sidebar.text_area(
                "部分一致で無視する文字列（1行に1つ）",
                value="\n".join(DEFAULT_IGNORED_HEADERS_CONTAIN),
                height=150
            )
            ignored_contain = [line.strip() for line in ignored_contain_text.split('\n') if line.strip()]
            
            # その他の設定
            st.sidebar.subheader("📈 グラフ設定")
            free_text_threshold = st.sidebar.slider(
                "自由記述として扱う選択肢の最大数",
                min_value=5,
                max_value=50,
                value=DEFAULT_FREE_TEXT_THRESHOLD,
                help="この数を超える選択肢がある場合、グラフ化せずに自由記述として表示します"
            )
            
            # 自由記述の表示設定
            st.sidebar.subheader("📝 自由記述表示設定")
            max_display_answers = st.sidebar.slider(
                "表示する回答の最大数",
                min_value=20,
                max_value=200,
                value=100,
                help="自由記述で表示する回答の最大数を設定します"
            )
            
            max_text_length = st.sidebar.slider(
                "回答テキストの最大文字数",
                min_value=50,
                max_value=500,
                value=200,
                help="各回答で表示する最大文字数を設定します"
            )
            
            # PDFファイル名
            pdf_filename = st.sidebar.text_input(
                "PDFファイル名",
                value="アンケート結果レポート.pdf"
            )
            
            # 処理対象の列を表示
            processed_columns = [col for col in df.columns if not should_ignore_column(col, ignored_exact, ignored_contain)]
            st.sidebar.subheader("📊 処理対象の列")
            st.sidebar.write(f"処理対象: {len(processed_columns)}列")
            
            with st.sidebar.expander("処理対象の列名を表示"):
                for col in processed_columns:
                    st.write(f"• {col}")
            
            # レポート生成ボタン
            if st.button("🚀 PDFレポートを生成", type="primary"):
                if not processed_columns:
                    st.error("❌ 処理対象の列がありません。設定を確認してください。")
                else:
                    with st.spinner("レポートを生成中..."):
                        try:
                            pdf_buffer, processed_questions = generate_report(
                                df, ignored_exact, ignored_contain, free_text_threshold, max_display_answers, max_text_length, pdf_filename
                            )
                            
                            st.success(f"🎉 レポートが完成しました！ (処理した質問数: {processed_questions})")
                            
                            # ダウンロードボタン
                            st.download_button(
                                label="📥 PDFをダウンロード",
                                data=pdf_buffer,
                                file_name=pdf_filename,
                                mime="application/pdf"
                            )
                            
                        except Exception as e:
                            st.error(f"❌ エラーが発生しました: {str(e)}")
            
        except Exception as e:
            st.error(f"❌ CSVファイルの読み込みに失敗しました: {str(e)}")
    
    else:
        st.info("👆 CSVファイルをアップロードしてください")
        
        # 使用方法の説明
        with st.expander("📖 使用方法"):
            st.markdown("""
            1. **CSVファイルをアップロード**: アンケート結果のCSVファイルを選択してください
            2. **設定を調整**: サイドバーで無視する列やグラフ設定を調整できます
            3. **レポート生成**: 「PDFレポートを生成」ボタンをクリックしてください
            4. **ダウンロード**: 生成されたPDFファイルをダウンロードできます
            
            ### 機能
            - 📊 自動的にグラフ化（選択肢が少ない場合）
            - 📝 自由記述として表示（選択肢が多い場合）
            - 🎨 モダンなデザインのPDFレポート
            - ⚙️ 柔軟な設定オプション
            """)

if __name__ == "__main__":
    main()