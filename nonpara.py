import streamlit as st
import numpy as np
import pandas as pd
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager

# --- 日本語フォント対応 ---
def set_japanese_font():
    try:
        import japanize_matplotlib
        return
    except ImportError:
        pass
    candidates = ['IPAexGothic', 'IPAPGothic', 'Noto Sans CJK JP',
                  'Hiragino Sans', 'Hiragino Maru Gothic Pro', 'MS Gothic', 
                  'Yu Gothic', 'Meiryo']
    available = {f.name for f in font_manager.fontManager.ttflist}
    for font in candidates:
        if font in available:
            plt.rcParams['font.family'] = font
            return
set_japanese_font()

# ==========================================
# ページ設定とタイトル
# ==========================================
st.set_page_config(page_title="第4章 ノンパラメトリック検定", layout="wide")

st.title("第4章 ノンパラメトリック検定「正規分布を仮定できないときの選択肢」")
st.markdown("""
農業や生物のデータには、「極端な外れ値がある」「左右非対称に歪んでいる」など、**t検定や分散分析の前提（正規分布）を満たさない**ことが多々あります。
このアプリでは、データの「実際の値」ではなく**「順位」**を使うことで、外れ値のノイズに負けずに差を見つけ出す**ノンパラメトリック検定の圧倒的な強さ（ロバスト性）**を体験します。
""")

tab1, tab2, tab3, tab4 = st.tabs([
    "🛡️ 1. 外れ値とU検定 (2群)", 
    "🌪️ 2. 歪んだ分布とK-W検定 (3群以上)", 
    "📊 3. 実データ解析ツール (CSV対応)", 
    "📖 4. 統計の基礎知識とコード"
])

# ==========================================
# タブ1: マン・ホイットニーのU検定（外れ値シミュレーター）
# ==========================================
with tab1:
    st.header("🛡️ 外れ値に対する強さ（マン・ホイットニーのU検定）")
    st.markdown("通常であれば「明らかに差がある」2つのグループに、**極端な外れ値（異常値）がたった1つ混ざっただけで、t検定がどれほど脆く崩壊するか**を観察してください。")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ 外れ値スライダー")
        st.info("👇 標準品種の1株だけが、異常な大きさ（外れ値）になったと仮定して、スライダーを右に動かしてください。")
        
        # 確実に差が出るベースデータを固定シードで生成
        np.random.seed(42)
        base_a = np.random.normal(500, 30, 20)  # 標準品種 (平均500)
        base_b = np.random.normal(530, 30, 20)  # 新系統 (平均530)
        
        outlier_val = st.slider("⚠️ 標準品種のデータ[1つ目]の値を変更 (g)", 400, 1500, 500, step=50)
        
        data_a = base_a.copy()
        data_b = base_b.copy()
        data_a[0] = outlier_val # 1つだけ外れ値に変更
        
        # 検定の実行
        t_stat, p_t = stats.ttest_ind(data_a, data_b, equal_var=False)
        u_stat, p_u = stats.mannwhitneyu(data_a, data_b, alternative='two-sided')
        
        st.markdown("### 📊 リアルタイム検定結果")
        
        # t検定の結果表示
        if p_t < 0.05:
            st.success(f"**❌ t検定 (p={p_t:.3f})**：有意差あり！")
        else:
            st.error(f"**❌ t検定 (p={p_t:.3f})**：有意差なし… (外れ値に騙されて差を見失いました)")
            
        # U検定の結果表示
        if p_u < 0.05:
            st.success(f"**🛡️ U検定 (p={p_u:.3f})**：有意差あり！ (外れ値を無視して正しく差を見抜いています)")
        else:
            st.error(f"**🛡️ U検定 (p={p_u:.3f})**：有意差なし")

    with col2:
        df_u = pd.DataFrame({
            "品種": ["標準品種"] * 20 + ["新系統"] * 20,
            "収量 (g)": np.concatenate([data_a, data_b])
        })
        
        # 可視化: データの動き
        fig_u = px.strip(df_u, x="品種", y="収量 (g)", color="品種", stripmode="overlay", title="収量データの分布（ドットプロット）")
        fig_u.add_hline(y=data_a.mean(), line_dash="dot", line_color="blue", annotation_text=f"標準の平均: {data_a.mean():.0f}g", annotation_position="bottom right")
        fig_u.add_hline(y=data_b.mean(), line_dash="dot", line_color="red", annotation_text=f"新系統の平均: {data_b.mean():.0f}g", annotation_position="top right")
        fig_u.update_traces(marker=dict(size=10, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(fig_u, use_container_width=True)
        
        st.caption("💡 **解説**: スライダーを動かすと、青い点（標準品種）の1つが上に飛び抜けます。すると青の平均線が引き上げられ、さらに「データのバラツキ（分散）」が爆発します。t検定はこの平均と分散を使って計算するため、**たった1つの外れ値でパニックになり「差がない」と誤判定**してしまいます。一方、U検定は「順位（1番大きい）」しか見ないため、値が1500になっても全く影響を受けません。")

# ==========================================
# タブ2: クラスカル・ウォリス検定
# ==========================================
with tab2:
    st.header("🌪️ 歪んだ分布に対する強さ（クラスカル・ウォリス検定）")
    st.markdown("農業によくある「害虫の数」など、**ゼロ付近に集中し、ごく一部だけが極端に多い（右に裾を引く歪んだデータ）**での、分散分析(ANOVA)の弱さを観察します。")
    
    col3, col4 = st.columns([1, 2])
    
    with col3:
        st.subheader("データ設定")
        st.info("👇 意図的に歪んだ（対数正規分布のような）固定データを用意しました。ボタンを押して、検定結果の違いを確認してください。")
        
        # 確実にANOVAが騙されてK-Wが勝つ、歪んだ配列を固定で用意
        base_A = np.array([0, 1, 1, 2, 2, 3, 4, 5, 8, 12, 25, 40, 70, 120, 250]) # 中央値3, 平均36
        base_B = np.array([3, 4, 5, 7, 9, 12, 15, 20, 28, 40, 65, 90, 150, 220, 350]) # 中央値20, 平均67
        base_C = np.array([8, 12, 15, 20, 25, 30, 40, 50, 65, 85, 120, 180, 280, 400, 600]) # 中央値50, 平均128
        
        if st.button("📊 このデータで検定を実行する", type="primary"):
            f_stat, p_f = stats.f_oneway(base_A, base_B, base_C)
            h_stat, p_kw = stats.kruskal(base_A, base_B, base_C)
            
            st.markdown("### 📊 検定結果の比較")
            
            st.markdown("#### ❌ 分散分析 (ANOVA)")
            st.write(f"**p値 = {p_f:.4f}**")
            if p_f < 0.05:
                st.success("有意差あり (p < 0.05)")
            else:
                st.error("【判定】有意差なし (p >= 0.05)")
            st.markdown("↑ 極端な値によって分散（バラツキ）が巨大化しているため、**「グループ間の差なのか、ただのバラツキなのか分からない」と判定を放棄（見逃し）**してしまっています。")
            
            st.markdown("---")
            
            st.markdown("#### 🌪️ クラスカル・ウォリス検定")
            st.write(f"**p値 = {p_kw:.4f}**")
            if p_kw < 0.05:
                st.success("【判定】有意差あり (p < 0.05) 🎉")
            else:
                st.error("有意差なし (p >= 0.05)")
            st.markdown("↑ 実際の数値（350匹など）ではなく**「順位」**に変換して計算するため、少数の極端な値に引っ張られず、**「全体的に薬剤Cの方が虫が多い」という真実を正しく検出**しています。")

    with col4:
        df_kw = pd.DataFrame({
            "処理区": ["薬剤A"] * 15 + ["薬剤B"] * 15 + ["薬剤C"] * 15,
            "害虫の数 (匹)": np.concatenate([base_A, base_B, base_C])
        })
        
        # 可視化: 箱ひげ図
        fig_kw = px.box(df_kw, x="処理区", y="害虫の数 (匹)", color="処理区", points="all", title="害虫発生数の分布（激しく歪んだ非正規分布）")
        st.plotly_chart(fig_kw, use_container_width=True)

# ==========================================
# タブ3: 実データ解析ツール (ノンパラメトリック)
# ==========================================
with tab3:
    st.header("📊 ノンパラメトリック検定 解析ツール")
    st.markdown("自身の実験データ（CSV）を読み込んで、群数に応じて適切なノンパラメトリック検定（U検定 または K-W検定）を自動で行います。")

    data_source = st.radio(
        "データの入力方法を選んでください：", 
        ["🐞 組み込みのサンプルデータで試す（害虫調査データ）", "📁 自分のCSVをアップロードする"],
        key="data_source_np"
    )

    df_real = None

    if "組み込み" in data_source:
        np.random.seed(123)
        df_real = pd.DataFrame({
            '薬剤': ['無処理', '薬剤X', '薬剤Y'] * 10,
            '害虫数': np.concatenate([
                np.random.lognormal(2.5, 1.0, 10),
                np.random.lognormal(1.5, 0.8, 10),
                np.random.lognormal(0.5, 0.5, 10)
            ])
        })
        df_real['害虫数'] = df_real['害虫数'].astype(int)
        st.success("✅ サンプルデータを読み込みました。")
    else:
        uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv", key="uploader_np")
        if uploaded_file is not None:
            try:
                df_real = pd.read_csv(uploaded_file, encoding='shift_jis')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df_real = pd.read_csv(uploaded_file, encoding='utf-8')
            st.success("✅ CSVを読み込みました。")

    if df_real is not None:
        st.subheader("1. データプレビュー")
        st.dataframe(df_real.head(10))

        col1, col2 = st.columns(2)
        with col1:
            numeric_cols = df_real.select_dtypes(include=['number']).columns.tolist()
            yld_idx = df_real.columns.get_loc('害虫数') if '害虫数' in df_real.columns else (df_real.columns.get_loc(numeric_cols[0]) if numeric_cols else 0)
            target_col = st.selectbox("目的変数（数値データ）", df_real.columns, index=yld_idx)
        with col2:
            var_idx = df_real.columns.get_loc('薬剤') if '薬剤' in df_real.columns else 0
            factor_x = st.selectbox("比較するグループ（カテゴリ）", df_real.columns, index=var_idx)

        if st.button("ノンパラメトリック検定を実行", type="primary"):
            try:
                df_clean = df_real.copy()
                df_clean[target_col] = pd.to_numeric(df_clean[target_col], errors='coerce')
                df_clean = df_clean.dropna(subset=[target_col, factor_x]).copy()

                groups = df_clean[factor_x].unique()
                k = len(groups)

                if k < 2:
                    st.error("【エラー】比較するグループが2つ以上必要です。")
                else:
                    st.header("📈 解析結果報告書")
                    
                    sns.set_theme(style="whitegrid")
                    set_japanese_font()

                    data_list = [df_clean[df_clean[factor_x] == g][target_col].values for g in groups]

                    if k == 2:
                        st.subheader(f"🛡️ マン・ホイットニーのU検定 (2群の比較)")
                        u_stat, p_val = stats.mannwhitneyu(data_list[0], data_list[1], alternative='two-sided')
                        
                        st.write(f"- **比較するグループ**: {groups[0]} vs {groups[1]}")
                        st.write(f"- **U統計量**: {u_stat:.3f}")
                        st.write(f"- **p値**: {p_val:.5f}")
                        
                        if p_val < 0.05:
                            st.success(f"🎉 **有意差あり (p < 0.05)**：{groups[0]} と {groups[1]} の間には統計的に有意な差があります。")
                        else:
                            st.warning(f"🤔 **有意差なし (p >= 0.05)**：2つのグループ間に有意な差は認められませんでした。")
                            
                    else:
                        st.subheader(f"🌪️ クラスカル・ウォリス検定 ({k}群以上の比較)")
                        h_stat, p_val = stats.kruskal(*data_list)
                        
                        st.write(f"- **比較するグループ**: {', '.join(str(g) for g in groups)}")
                        st.write(f"- **H統計量**: {h_stat:.3f}")
                        st.write(f"- **p値**: {p_val:.5f}")
                        
                        if p_val < 0.05:
                            st.success("🎉 **有意差あり (p < 0.05)**：少なくとも1つのグループ間に統計的に有意な差があります。")
                        else:
                            st.warning("🤔 **有意差なし (p >= 0.05)**：グループ間に有意な差は認められませんでした。")

                    st.divider()
                    
                    st.subheader("📊 データの分布と中央値")
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    sns.boxplot(x=factor_x, y=target_col, data=df_clean, ax=ax, color='#f0f0f0', 
                                medianprops={'color':'red', 'linewidth':2}, showfliers=False)
                    sns.stripplot(x=factor_x, y=target_col, data=df_clean, ax=ax, color='black', alpha=0.6, jitter=True)
                    
                    ax.set_ylabel(target_col, fontsize=12)
                    ax.set_xlabel(factor_x, fontsize=12)
                    ax.set_title("赤線：中央値 (Median)  ※ノンパラでは平均より中央値が重要です", fontsize=14, color='red', fontweight='bold')
                    st.pyplot(fig)

            except Exception as e:
                st.error(f"解析中にエラーが発生しました: {e}")

# ==========================================
# タブ4: 統計用語の解説とコード
# ==========================================
with tab4:
    st.header("📖 ノンパラメトリック検定の基礎知識")
    
    st.markdown("### パラメトリックとノンパラメトリックの違い")
    st.info("""
    * **パラメトリック検定（t検定、分散分析など）**:
      データが「正規分布（きれいな釣り鐘型）」に従うことを前提として、**平均値と分散**を使って計算します。前提を満たす場合は検出力が高いですが、外れ値に非常に弱いです。
    * **ノンパラメトリック検定（U検定、K-W検定など）**:
      分布の形を前提としません。実際の数値ではなく、データを小さい順に並べた**「順位（ランク）」**を使って計算します。そのため、外れ値や極端に歪んだ分布に対して強い（ロバスト）という特徴があります。
    """)
    
    st.markdown("### どんな時にノンパラメトリック検定を使うべき？")
    st.success("""
    1. **明確な外れ値がある**が、記録ミスではなく事実なので削除できない場合。
    2. **データが極端に歪んでいる**場合。（例：害虫の数、病気の発症度合い、発芽日数など）
    3. そもそも数値の大きさに意味がない**順序データ**の場合。（例：食味スコア 1〜5段階評価、病斑指数など）
    4. **サンプルサイズが非常に小さい**（各群 n < 5 程度）ため、正規分布かどうかすら確認できない場合。
    """)

    st.markdown("### 検定手法の対応表")
    st.table(pd.DataFrame({
        "目的": ["2群の比較（独立）", "3群以上の比較（独立）", "2群の比較（対応あり・前後比較）"],
        "パラメトリック検定 (正規分布を前提)": ["ウェルチのt検定", "一元配置分散分析 (ANOVA)", "対応のあるt検定"],
        "ノンパラメトリック検定 (順位を使用)": ["マン・ホイットニーのU検定", "クラスカル・ウォリス検定", "ウィルコクソンの符号付順位検定"]
    }))

    st.markdown("---")
    st.markdown("### 💻 【参考】R言語での実行スクリプト")
    
    st.code("""
# 1. マン・ホイットニーのU検定 (2群の比較)
# Rでは wilcox.test という関数を使います
u_result <- wilcox.test(Yield ~ Variety, data = data_u, exact = FALSE)
print(u_result)

# 2. クラスカル・ウォリス検定 (3群以上の比較)
kw_result <- kruskal.test(PestCount ~ Treatment, data = data_kw)
print(kw_result)

# 3. ノンパラメトリックの多重比較 (K-W検定で有意差が出た後)
# dunn.test パッケージの Dunn検定（ボンフェローニ調整付き）などがよく使われます
# install.packages("dunn.test")
library(dunn.test)
dunn.test(data_kw$PestCount, data_kw$Treatment, method="bonferroni")
    """, language="r")