import streamlit as st
import anthropic
import pandas as pd
import plotly.graph_objects as go
import json

st.set_page_config(page_title="Cash Reality Check", layout="wide", page_icon="💰")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&family=Instrument+Serif:ital@0;1&display=swap');
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
  .hero { background: #0e0e0d; padding: 48px 40px; border-radius: 4px; margin-bottom: 32px; }
  .hero h1 { font-family: 'Instrument Serif', serif; font-size: 2.4rem; color: #f7f4ee; letter-spacing: -1px; margin-bottom: 8px; }
  .hero p { color: rgba(247,244,238,0.55); font-size: 15px; font-weight: 300; margin-bottom: 0; }
  .runway-banner { padding: 24px 28px; border-radius: 4px; margin-bottom: 28px; }
  .runway-danger { background: #fee2e2; border-left: 4px solid #c13b20; }
  .runway-warning { background: #fff3cd; border-left: 4px solid #f59e0b; }
  .runway-safe { background: #e8f5f2; border-left: 4px solid #2d7d6f; }
  .runway-n { font-family: 'Instrument Serif', serif; font-size: 3rem; letter-spacing: -2px; line-height: 1; }
  .runway-danger .runway-n { color: #c13b20; }
  .runway-warning .runway-n { color: #b45309; }
  .runway-safe .runway-n { color: #2d7d6f; }
  .runway-label { font-size: 13px; color: #3a3a38; font-weight: 400; margin-top: 6px; }
  .cfo-box { background: #0e0e0d; color: #f7f4ee; padding: 28px 32px; border-radius: 4px; margin: 20px 0; }
  .cfo-box h3 { font-family: 'Instrument Serif', serif; font-size: 1.4rem; color: #f7f4ee; margin-bottom: 16px; }
  .cfo-item { font-size: 14px; color: rgba(247,244,238,0.7); line-height: 1.7; padding: 8px 0; border-bottom: 1px solid rgba(247,244,238,0.08); display: flex; gap: 10px; }
  .cfo-item:last-child { border-bottom: none; }
  .systems-box { background: #f5ebe7; border-left: 3px solid #c13b20; padding: 24px 28px; border-radius: 0 4px 4px 0; margin: 20px 0; }
  .systems-box h3 { font-family: 'Instrument Serif', serif; font-size: 1.3rem; color: #0e0e0d; margin-bottom: 12px; }
  .systems-item { font-size: 14px; color: #3a3a38; line-height: 1.7; padding: 6px 0; display: flex; gap: 10px; }
  .result-section { background: #f7f4ee; border-left: 3px solid #c13b20; padding: 28px 32px; border-radius: 0 4px 4px 0; margin: 20px 0; line-height: 1.8; }
  .footer-line { font-size: 14px; font-style: italic; color: #3a3a38; text-align: center; padding: 16px; border-top: 1px solid rgba(14,14,13,0.1); margin-top: 32px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>Cash Reality Check</h1>
  <p>Enter your numbers. Find out exactly when your cash runs out and what to do about it.</p>
</div>
""", unsafe_allow_html=True)

# INPUT MODE
input_mode = st.radio(
    "How would you like to enter your data?",
    ["Enter numbers manually", "Upload a CSV file"],
    horizontal=True
)

df = None
manual_data = None
current_balance = 0
currency = "SGD"

if input_mode == "Upload a CSV file":
    st.markdown("#### Upload your transaction history")
    st.caption("CSV should have columns: date, description, amount (positive = income, negative = expense).")
    col1, col2 = st.columns(2)
    with col1:
        currency = st.selectbox("Currency", ["SGD", "USD", "INR", "MYR", "IDR", "PHP", "THB"])
    with col2:
        current_balance = st.number_input("Current bank balance", min_value=0, value=50000, step=1000)
    uploaded = st.file_uploader("Upload CSV", type="csv")
    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            st.success(f"Loaded {len(df)} transactions")
            st.dataframe(df.head(8), use_container_width=True)
        except Exception as e:
            st.error(f"Could not read file: {e}")
    sample = pd.DataFrame({
        "date": ["2026-01-01","2026-01-05","2026-01-10","2026-01-15","2026-01-20","2026-02-01","2026-02-05","2026-02-10"],
        "description": ["Client payment","Office rent","Salaries","Software subscriptions","Client payment","Client payment","Marketing spend","Client payment"],
        "amount": [15000,-3500,-12000,-800,8000,20000,-2000,12000]
    })
    st.download_button("Download sample CSV", sample.to_csv(index=False), "sample_transactions.csv", "text/csv")

else:
    st.markdown("#### Your monthly financials")
    col1, col2 = st.columns(2)
    with col1:
        currency = st.selectbox("Currency", ["SGD", "USD", "INR", "MYR", "IDR", "PHP", "THB"])
    with col2:
        current_balance = st.number_input("Current bank balance", min_value=0, value=50000, step=1000)

    st.markdown("**Monthly Income**")
    col1, col2, col3 = st.columns(3)
    with col1:
        rev_recurring = st.number_input("Recurring revenue", min_value=0, value=30000, step=500)
    with col2:
        rev_project = st.number_input("Project or one-off income", min_value=0, value=10000, step=500)
    with col3:
        rev_other = st.number_input("Other income", min_value=0, value=0, step=500)

    st.markdown("**Monthly Expenses**")
    col1, col2, col3 = st.columns(3)
    with col1:
        exp_salaries = st.number_input("Salaries and payroll", min_value=0, value=20000, step=500)
        exp_rent = st.number_input("Rent and office", min_value=0, value=3000, step=500)
    with col2:
        exp_software = st.number_input("Software and tools", min_value=0, value=1500, step=100)
        exp_marketing = st.number_input("Marketing and sales", min_value=0, value=2000, step=500)
    with col3:
        exp_ops = st.number_input("Operations", min_value=0, value=1000, step=500)
        exp_other = st.number_input("Other expenses", min_value=0, value=500, step=500)

    st.markdown("**Growth assumptions**")
    col1, col2 = st.columns(2)
    with col1:
        revenue_growth = st.slider("Expected monthly revenue growth %", -20, 50, 5)
    with col2:
        expense_growth = st.slider("Expected monthly expense growth %", -10, 30, 2)

    total_income = rev_recurring + rev_project + rev_other
    total_expenses = exp_salaries + exp_rent + exp_software + exp_marketing + exp_ops + exp_other
    monthly_net = total_income - total_expenses

    manual_data = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "revenue_growth": revenue_growth,
        "expense_growth": expense_growth,
        "breakdown": {
            "salaries": exp_salaries,
            "rent": exp_rent,
            "software": exp_software,
            "marketing": exp_marketing,
            "ops": exp_ops,
            "other": exp_other
        }
    }

    # RUNWAY BANNER — immediate, before they click anything
    if total_expenses > 0:
        if monthly_net < 0:
            runway_days = int((current_balance / abs(monthly_net)) * 30)
            banner_class = "runway-danger" if runway_days < 60 else "runway-warning"
            message = f"At current burn rate, you have approximately {runway_days} days before cash runs out."
        else:
            runway_days = None
            banner_class = "runway-safe"
            message = f"You are cash flow positive by {currency} {monthly_net:,} per month. Keep an eye on your growth assumptions."

        if runway_days:
            st.markdown(f"""
            <div class="runway-banner {banner_class}">
              <div class="runway-n">{runway_days} days</div>
              <div class="runway-label">{message}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="runway-banner {banner_class}">
              <div class="runway-n">Positive</div>
              <div class="runway-label">{message}</div>
            </div>
            """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Monthly Income", f"{currency} {total_income:,}")
    col2.metric("Monthly Expenses", f"{currency} {total_expenses:,}")
    col3.metric("Monthly Net", f"{currency} {monthly_net:,}")

business_context = st.text_area(
    "Optional: anything specific about your business",
    placeholder="e.g. We have 2 enterprise clients. Big contract renewal in 60 days. Hiring 3 people next month...",
    height=60
)

if st.button("Run Cash Reality Check", type="primary"):

    if manual_data:
        data_summary = f"""
Monthly income: {currency} {manual_data['total_income']:,}
Monthly expenses: {currency} {manual_data['total_expenses']:,}
Monthly net: {currency} {manual_data['total_income'] - manual_data['total_expenses']:,}
Current balance: {currency} {current_balance:,}
Revenue growth assumption: {manual_data['revenue_growth']}% per month
Expense growth assumption: {manual_data['expense_growth']}% per month
Expense breakdown: {json.dumps(manual_data['breakdown'])}
"""
        months = []
        bal = current_balance
        inc = manual_data['total_income']
        exp = manual_data['total_expenses']
        for i in range(1, 4):
            inc = inc * (1 + manual_data['revenue_growth']/100)
            exp = exp * (1 + manual_data['expense_growth']/100)
            bal = bal + inc - exp
            months.append({
                "month": f"Month {i}",
                "income": round(inc),
                "expenses": round(exp),
                "net": round(inc - exp),
                "balance": round(bal)
            })

    elif df is not None:
        try:
            if 'amount' in df.columns:
                total_in = df[df['amount'] > 0]['amount'].sum()
                total_out = abs(df[df['amount'] < 0]['amount'].sum())
                months_count = max(1, len(df) / 30)
                avg_monthly_in = total_in / months_count
                avg_monthly_out = total_out / months_count
            else:
                avg_monthly_in = 30000
                avg_monthly_out = 25000
            data_summary = f"""
Average monthly income: {currency} {avg_monthly_in:,.0f}
Average monthly expenses: {currency} {avg_monthly_out:,.0f}
Current balance: {currency} {current_balance:,}
Total transactions analysed: {len(df)}
"""
            months = []
            bal = current_balance
            for i in range(1, 4):
                net = avg_monthly_in - avg_monthly_out
                bal = bal + net
                months.append({
                    "month": f"Month {i}",
                    "income": round(avg_monthly_in),
                    "expenses": round(avg_monthly_out),
                    "net": round(net),
                    "balance": round(bal)
                })
        except:
            st.error("Could not process the CSV. Please check the format.")
            st.stop()
    else:
        st.warning("Please upload a CSV or enter your numbers above.")
        st.stop()

    with st.spinner("Running your cash reality check..."):

        # CHART
        st.markdown("### 90-Day Cash Position")
        chart_data = pd.DataFrame([
            {"Period": "Now", "Balance": current_balance},
            {"Period": months[0]["month"], "Balance": months[0]["balance"]},
            {"Period": months[1]["month"], "Balance": months[1]["balance"]},
            {"Period": months[2]["month"], "Balance": months[2]["balance"]},
        ])
        colors = ["#2d7d6f" if b > 0 else "#c13b20" for b in chart_data["Balance"]]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=chart_data["Period"],
            y=chart_data["Balance"],
            marker_color=colors,
            text=[f"{currency} {b:,}" for b in chart_data["Balance"]],
            textposition="outside"
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="#c13b20", annotation_text="Zero cash")
        fig.update_layout(
            plot_bgcolor="#f7f4ee", paper_bgcolor="#f7f4ee",
            font_family="DM Sans", showlegend=False, height=300,
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        # MONTH BREAKDOWN
        st.markdown("### Month by Month")
        cols = st.columns(3)
        for i, m in enumerate(months):
            with cols[i]:
                st.metric(m["month"] + " Income", f"{currency} {m['income']:,}")
                st.metric("Expenses", f"{currency} {m['expenses']:,}")
                st.metric("Closing Balance", f"{currency} {m['balance']:,}")

        # AI ANALYSIS
        prompt = f"""You are a blunt, experienced CFO advisor. You have seen hundreds of SME businesses fail because they ran out of visibility before they ran out of cash. You do not sugarcoat.

Business data:
{data_summary}

90-day projection:
{json.dumps(months, indent=2)}

{f'Business context: {business_context}' if business_context else ''}

Provide your analysis in exactly this structure:

## Cash Position Headline
One sentence. Blunt. Tell them what is actually happening.

## What I Would Worry About As Your CFO
3 to 4 specific concerns. Each one should be concrete, not generic. Format as short sharp bullets. These should feel like things a CFO would say privately in a board meeting, not in a polished report.

## The 3 Things That Will Kill You Before You Expect Them To
Specific, sequenced risks with rough timeframes. Not generic advice.

## What You Should Do In The Next 30 Days
3 concrete actions. Prioritised. Tell them exactly what to do first.

## What System Should Actually Exist Here
3 specific systems or processes this business needs that almost certainly do not exist yet. Frame each as: what it does, why it matters right now.

Be direct. Be specific. Sound like someone who has seen this exact situation before and knows how it ends if nothing changes."""

        try:
            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
            message = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1400,
                messages=[{"role": "user", "content": prompt}]
            )
            analysis = message.content[0].text

            st.markdown(f"""
            <div class="result-section">
            {analysis}
            </div>
            """, unsafe_allow_html=True)

            report = f"Cash Reality Check\n{'='*40}\n\n{data_summary}\n\n90-Day Projection:\n{json.dumps(months, indent=2)}\n\nCFO Analysis:\n{analysis}"
            st.download_button("Download Full Report", report, "cash_reality_check.txt", "text/plain")

            # SHARE CTA
            st.info("Send this to your co-founder or finance lead. Most cash crises are visible weeks before they happen. Most teams just do not look.")

        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.markdown("""
<div class="footer-line">
  Most businesses do not run out of money slowly. They run out of visibility first.
</div>
""", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center; padding:12px 0 24px;'>
  <p style='font-size:13px; color:#7a7a76;'>Built by <strong>Bhavani Susmitha</strong> · IIM Ahmedabad · Ex-Revolut · <a href="https://www.linkedin.com/in/bhavanisusmitha" target="_blank" style="color:#c13b20;">LinkedIn</a></p>
</div>
""", unsafe_allow_html=True)