import streamlit as st
import pandas as pd
import json
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Page Config
st.set_page_config(page_title="Brand Insights Dashboard", layout="wide")

# Load the data (Pre-calculated in process_data.py)
@st.cache_data
def load_data():
    with open('data.json', 'r') as f:
        data = json.load(f)
    
    # Convert reviews to DataFrame
    df_reviews = pd.DataFrame(data['reviews'])
    df_reviews['date'] = pd.to_datetime(df_reviews['date'])
    
    return data['products'], data['testimonials'], df_reviews

products, testimonials, df_reviews = load_data()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Products", "Testimonials", "Reviews"])

# --- PRODUCTS PAGE ---
if page == "Products":
    st.header("🛒 Scraped Products")
    df_p = pd.DataFrame(products)
    df_p.index = df_p.index + 1 
    df_p.index.name = "ID"
    st.dataframe(df_p, use_container_width=True)

# --- TESTIMONIALS PAGE ---
elif page == "Testimonials":
    st.header("💬 Customer Testimonials")
    for i, t in enumerate(testimonials, start=1):
        with st.chat_message("user"):
            st.write(f"**Testimonial {i}** ({t['author']}): {t['text']}")

# --- REVIEWS PAGE (Now using pre-calculated Sentiment) ---
elif page == "Reviews":
    st.header("📊 Review Sentiment Analysis")
    
    # 1. Month Selection Slider
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    selected_month_name = st.select_slider("Select Month (2023)", options=months)
    month_index = months.index(selected_month_name) + 1
    
    # 2. Filter Data
    filtered_df = df_reviews[df_reviews['date'].dt.month == month_index].copy()
    
    if filtered_df.empty:
        st.warning(f"No reviews found for {selected_month_name} 2023.")
    else:
        # 3. Visualization: Bar Chart
        st.subheader(f"Sentiment Split for {selected_month_name}")
        
        # We no longer run the pipeline here! 
        # We use the 'Sentiment' column already in your data.json
        sentiment_counts = filtered_df['Sentiment'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'count']
        
        # Calculate average confidence from existing data
        avg_confidence = filtered_df.groupby('Sentiment')['Confidence'].mean().reset_index()
        viz_df = sentiment_counts.merge(avg_confidence, on='Sentiment')
        
        fig = px.bar(viz_df, x='Sentiment', y='count', 
                     color='Sentiment',
                     hover_data=['Confidence'],
                     labels={'count': 'Number of Reviews', 'Confidence': 'Avg Confidence'},
                     title="Positive vs Negative Counts")
        st.plotly_chart(fig, use_container_width=True)

        # 4. Word Cloud
        st.subheader("Word Cloud")
        text_combined = " ".join(filtered_df['text'].astype(str).tolist())
        wordcloud = WordCloud(background_color='white', width=800, height=400).generate(text_combined)
        
        fig_wc, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig_wc)

        # 5. Show raw data list
        st.subheader("Filtered Reviews List")
        st.table(filtered_df[['date', 'text', 'Sentiment', 'Confidence']])