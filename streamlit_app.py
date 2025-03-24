import streamlit as st
import gspread
import toml
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import uuid

def get_color(val):
    return "rgb(255,171,171)" if val < 0 else "rgb(131,201,255)"

def return_center_name(name):
    CENTER_NAMES = {"center_1": "동탄1센터", "center_2": "동탄2센터"}
    return CENTER_NAMES[name]

def title(year, month, center=None):
    if center:
        st.title(f"{year}년 {month}월 {center}")
    else:
        st.title(f"{year}년 {month}월 CJ 물류센터 손익 현황")


def total_dashboard(filtered_df,year, month):
    st.title(f"{year}년 {month}월 CJ 물류센터 물량 현황")

    tab1, tab2 = st.columns(2)

    with tab1:
        # ✅ 센터별 goods & army 파이차트
        c1_goods = filtered_df["center_1_goods"].astype(float).sum()
        c2_goods = filtered_df["center_2_goods"].astype(float).sum()
        c1_armys = filtered_df["center_1_army"].astype(float).sum()

        goods_pie = go.Figure(data=[go.Pie(
            labels=["동탄1센터 물자", "동탄2센터 물자", "동탄1센터 군물자"],
            values=[c1_goods, c2_goods, c1_armys],
            hole=0.3
        )])

        # 차트 하단 중앙에 타이틀 위치 조정
        goods_pie.update_layout(
            title_text="센터별 물자 & 군 공급 비율",
            title_x=0.5,
            title_y=0.95,   # 상단에 위치 (기본값은 0.9 정도)
            title_font_size=16
        )
        st.plotly_chart(goods_pie, use_container_width=True, key=str(uuid.uuid4()))
        
    with tab2:
        # ✅ 센터별 goods & army 파이차트
        c1_label = filtered_df["center_1_label"].astype(float).sum()
        c2_label = filtered_df["center_2_label"].astype(float).sum()

        goods_pie = go.Figure(data=[go.Pie(
            labels=["동탄1센터 라벨", "동탄2센터 라벨"],
            values=[c1_label, c2_label],
            hole=0.3
        )])

        # 차트 하단 중앙에 타이틀 위치 조정
        goods_pie.update_layout(
            title_text="센터별 라벨비율",
            title_x=0.5,
            title_y=0.95,   # 상단에 위치 (기본값은 0.9 정도)
            title_font_size=16
        )
        st.plotly_chart(goods_pie, use_container_width=True, key=str(uuid.uuid4()))

    # 필요한 컬럼만 복사
    bar_df = filtered_df[[
        "date", "center_1_goods", "center_1_army", "center_1_label",
        "center_2_goods", "center_2_label"
    ]].copy()

    # melt를 통해 긴 포맷으로 변환
    melted = bar_df.melt(
        id_vars="date",
        value_vars=[
            "center_1_goods", "center_1_army", "center_1_label",
            "center_2_goods", "center_2_label"
        ],
        var_name="항목", value_name="값"
    )

    # 항목명 한글로 매핑
    label_map = {
        "center_1_goods": "동탄1 물자",
        "center_1_army": "동탄1 군",
        "center_1_label": "동탄1 라벨",
        "center_2_goods": "동탄2 물자",
        "center_2_label": "동탄2 라벨",
    }
    melted["항목"] = melted["항목"].map(label_map)

    # 스택형 막대그래프
    fig = px.bar(
        melted,
        x="date",
        y="값",
        color="항목",
        title="일자별 물자/군/라벨 스택형 그래프",
        barmode="stack"
    )

    fig.update_layout(xaxis_title="날짜", yaxis_title="합계 (단위: kg 또는 건)", bargap=0.1)


    st.plotly_chart(fig, use_container_width=True, key=str(uuid.uuid4()))
        
    # 🔁 통합 그래프
    if "center_1" in filtered_df.columns and "center_2" in filtered_df.columns:
        # st.title("통합 손익 (동탄1센터 + 동탄2센터)")
        title(year, month)

    filtered_df["통합 손익"] = filtered_df["center_1"] + filtered_df["center_2"]
    filtered_df["통합 누적"] = filtered_df["통합 손익"].cumsum()
    max_abs = max(abs(filtered_df["통합 손익"].min()), abs(filtered_df["통합 손익"].max()))

    min_val = filtered_df["통합 손익"].min()
    max_val = filtered_df["통합 손익"].max()
    total_val = filtered_df["통합 누적"].iloc[-1]
    avg_val = filtered_df["통합 손익"].mean()

    m1, m2, m3, m4 = st.columns(4)

    # 📉 최저 손익
    m1.markdown(f"📉 **최저 손익**<br><span style='color:{get_color(min_val)}; font-size:35px;'>{min_val:,.0f}</span>",unsafe_allow_html=True)
    # 📈 최고 손익
    m2.markdown(f"📈 **최고 손익**<br><span style='color:{get_color(max_val)}; font-size:35px;'>{max_val:,.0f}</span>",unsafe_allow_html=True)
    # 🔢 누적 손익
    m3.markdown(f"🔢 **누적 손익**<br><span style='color:{get_color(total_val)}; font-size:35px;'>{total_val:,.0f}</span>",unsafe_allow_html=True)
    # 📊 평균 손익
    m4.markdown(f"📊 **평균 손익**<br><span style='color:{get_color(avg_val)}; font-size:35px;'>{avg_val:,.0f}</span>",unsafe_allow_html=True)


    colors = ["rgb(131,201,255)" if val >= 0 else "rgb(255,171,171)" for val in filtered_df["통합 손익"]]

    fig = go.Figure()

    fig.add_trace(go.Bar(x=filtered_df["date"],y=filtered_df["통합 손익"],name="통합 일별 손익",marker_color=colors,yaxis="y"))
    fig.add_trace(go.Scatter(x=filtered_df["date"],y=filtered_df["통합 누적"],name="통합 누적 손익",mode="lines+markers",yaxis="y2",line=dict(width=5, dash="solid", color="rgb(1,104,201)"),marker=dict(size=9)))

    for x_val, y_val in zip(filtered_df["date"], filtered_df["통합 손익"]):
        label = f"{y_val:,.0f}만"
        offset = max_abs * 0.05 if y_val >= 0 else -max_abs * 0.05
        fig.add_annotation(
            x=x_val,
            y=y_val + offset,
            text=label,
            showarrow=False,
            textangle=-45,
        )

    fig.add_annotation(x=filtered_df["date"].iloc[-1],y=total_val,text=f"{total_val:,.0f}만",showarrow=False,yshift=10,)
    fig.update_layout(xaxis=dict(title="날짜", tickangle=-45),yaxis=dict(title="일별 손익 (만원)",range=[-max_abs * 1.2, max_abs * 1.2],rangemode="tozero"),yaxis2=dict(title="누적 손익 (만원)",side="right",overlaying="y",showgrid=False),height=650,hovermode="x unified")

    st.plotly_chart(fig, use_container_width=True, key=str(uuid.uuid4()))
    
    # ✅ 전체 월별 통합 손익 막대 그래프
    monthly_sum = df.groupby(["연", "월"])[["center_1", "center_2"]].sum().reset_index()
    monthly_sum["통합 손익"] = monthly_sum["center_1"] + monthly_sum["center_2"]

    # 누락된 월은 0으로 채우기
    full_range = pd.MultiIndex.from_product([
        sorted(df["연"].unique()),
        list(range(1, 13))
    ], names=["연", "월"])
    monthly_sum = monthly_sum.set_index(["연", "월"]).reindex(full_range, fill_value=0).reset_index()

    monthly_sum["기간"] = monthly_sum["연"].astype(str) + "-" + monthly_sum["월"].astype(str).str.zfill(2)
    monthly_sum["월라벨"] = monthly_sum["월"].astype(str) + "월"

    fig = px.bar(
        monthly_sum,
        x="월라벨",
        y="통합 손익",
        color="통합 손익",
        color_continuous_scale=["rgb(255,171,171)", "lightgrey", "rgb(131,201,255)"],
        height=500,
        text="통합 손익"  # ✅ 막대 위 숫자 표시
        
    )
    
        # "rgb(131,201,255)" if val >= 0 else "rgb(255,171,171)"
    fig.update_traces(texttemplate="%{text:,.0f}만", textposition="outside")
    
    fig.update_layout(
        xaxis_title="월",
        yaxis_title="통합 손익 (만원)",
        xaxis=dict(
            showline=True,
            categoryorder="array",
            categoryarray=[f"{m}월" for m in range(1, 13)],
            showgrid=True,
            
        ),
        yaxis=dict(
            showline=True,
            zeroline=True,
            linewidth=1,
            mirror=True,
            showgrid=True,
            zerolinewidth=5
        ),

        coloraxis_showscale=False
    )

    st.title(f"{year}년 전체 월별 통합 손익")
    st.plotly_chart(fig, use_container_width=True, key=str(uuid.uuid4()))



def center_dashboard(filtered_df, col,year, month):

    c_label = return_center_name(col)

    st.title(title(year, month,center=c_label))


    cumulative = filtered_df[col].cumsum()
    max_abs = max(abs(filtered_df[col].min()), abs(filtered_df[col].max()))
    min_val = filtered_df[col].min()
    max_val = filtered_df[col].max()
    total_val = cumulative.iloc[-1]
    avg_val = filtered_df[col].mean()

    m1, m2, m3, m4 = st.columns(4)
    # 📉 최저 손익
    m1.markdown(f"📉 **최저 손익**<br><span style='color:{get_color(min_val)}; font-size:35px;'>{min_val:,.0f}</span>",unsafe_allow_html=True)
    # 📈 최고 손익
    m2.markdown(f"📈 **최고 손익**<br><span style='color:{get_color(max_val)}; font-size:35px;'>{max_val:,.0f}</span>",unsafe_allow_html=True)
    # 🔢 누적 손익
    m3.markdown(f"🔢 **누적 손익**<br><span style='color:{get_color(total_val)}; font-size:35px;'>{total_val:,.0f}</span>",unsafe_allow_html=True)
    # 📊 평균 손익
    m4.markdown(f"📊 **평균 손익**<br><span style='color:{get_color(avg_val)}; font-size:35px;'>{avg_val:,.0f}</span>",unsafe_allow_html=True)

    colors = [
        "rgb(131,201,255)" if val >= 0 else "rgb(255,171,171)"
        for val in filtered_df[col]
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=filtered_df["date"],
        y=filtered_df[col],
        name=f"{c_label} 일별 손익",
        marker_color=colors,
        yaxis="y"
    ))

    fig.add_trace(go.Scatter(
        x=filtered_df["date"],
        y=cumulative,
        name=f"{c_label} 누적 손익",
        mode="lines+markers",
        yaxis="y2",
        line=dict(width=5, dash="solid", color="rgb(1,104,201)"),
        marker=dict(size=9)
    ))

    for x_val, y_val in zip(filtered_df["date"], filtered_df[col]):
        label = f"{y_val:,.0f}만"
        offset = max_abs * 0.05 if y_val >= 0 else -max_abs * 0.05
        fig.add_annotation(
            x=x_val,
            y=y_val + offset,
            text=label,
            showarrow=False,
            textangle=-45,
        )

    fig.add_annotation(
        x=filtered_df["date"].iloc[-1],
        y=total_val,
        text=f"{total_val:,.0f}만원",
        showarrow=False,
        yshift=10,
    )

    fig.update_layout(
        xaxis=dict(title="날짜", tickangle=-45),
        yaxis=dict(
            title="일별 손익 (만원)",
            range=[-max_abs * 1.2, max_abs * 1.2],
            rangemode="tozero"
        ),
        yaxis2=dict(
            title="누적 손익 (만원)",
            side="right",
            overlaying="y",
            showgrid=False
        ),
        height=650,
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True, key=str(uuid.uuid4()))
    st.divider()


if __name__ == "__main__":
    
    st.set_page_config(page_title="CJ 물류센터 손익", page_icon=":bar_chart:", layout="wide")

    # 🔐 Load secrets
    config = toml.load(".streamlit/secrets.toml")
    google_config = config["google_sheets"]

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info({
        "type": google_config["type"],
        "project_id": google_config["project_id"],
        "private_key_id": google_config["private_key_id"],
        "private_key": google_config["private_key"].replace("\\n", "\n"),
        "client_email": google_config["client_email"],
        "client_id": google_config["client_id"],
        "auth_uri": google_config["auth_uri"],
        "token_uri": google_config["token_uri"],
        "auth_provider_x509_cert_url": google_config["auth_provider_x509_cert_url"],
        "client_x509_cert_url": google_config["client_x509_cert_url"]
    }, scopes=scope)

    client = gspread.authorize(creds)
    SPREADSHEET_ID = "1gomjbrX0pULJ4njnV8NksMJoVddc23aHzEvmwi65iKA"
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet("시트1")

    # Load data
    data = sheet.get_all_values()
    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.set_index(df.columns[0])
    df = df.reset_index(drop=False)

    df.columns = df.columns.astype(str).str.strip()
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    
    
    # ➤ Convert to 만원
    for col in ["center_1", "center_2"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", "").astype(float)
            df[col] = df[col] / 10000
        else:
            st.warning(f"'{return_center_name[col]}' 컬럼이 없습니다.")

    # ➤ Parse date
    try:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        
        df["연"] = df["date"].dt.year.astype(int)
        df["월"] = df["date"].dt.month.astype(int)
    except Exception as e:
        st.error(f"날짜 변환 오류: {e}")
        
    # 📅 연/월 선택 필터
    st.logo("./logo.png", size='large',link="https://www.manpower.co.kr/",)
    st.sidebar.title("📆 날짜 필터")
    year_options = sorted(df["연"].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("연도 선택", year_options)

    month_options = sorted(df[df["연"] == selected_year]["월"].dropna().astype(int).unique())
    selected_month = st.sidebar.selectbox("월 선택", month_options)


    if st.sidebar.button("Reload"):
        filtered_df = df[(df["연"] == selected_year) & (df["월"] == selected_month)].copy()
    # 📋 필터 적용
    filtered_df = df[(df["연"] == selected_year) & (df["월"] == selected_month)].copy()
    
    
    tab1, tab2, tab3 = st.tabs(["통합정보", "통탄1센터", "동탄2센터"])

    with tab1:
        total_dashboard(filtered_df,selected_year, selected_month)
    
    with tab2:
        center_dashboard(filtered_df, "center_1",selected_year, selected_month)
    
    with tab3:
        center_dashboard(filtered_df, "center_2",selected_year, selected_month)
