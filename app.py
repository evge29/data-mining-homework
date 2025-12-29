import streamlit as st
import pandas as pd
import json
from transformers import pipeline
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Page Config
st.set_page_config(page_title="Brand Insights Dashboard", layout="wide")

# Load the data we scraped
@st.cache_data
def load_data():
    with open('data.json', 'r') as f:
        data = json.load(f)
    # Convert dates to datetime objects for filtering
    df_reviews = pd.DataFrame(data['reviews'])
    df_reviews['date'] = pd.to_datetime(df_reviews['date'])
    return data['products'], data['testimonials'], df_reviews

products, testimonials, df_reviews = load_data()

# Load Sentiment Model (Hugging Face)
@st.cache_resource
def load_sentiment_model():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

sentiment_pipeline = load_sentiment_model()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Products", "Testimonials", "Reviews"])

# --- PRODUCTS PAGE ---
if page == "Products":
    st.header("🛒 Scraped Products")
    
    # Create the DataFrame
    df_p = pd.DataFrame(products)
    
    # SHIFT THE INDEX: This is the fix for the numbering
    df_p.index = df_p.index + 1 
    
    # Rename the index to "ID" so it looks professional in the table
    df_p.index.name = "ID"
    
    # Display with the new index visible
    st.dataframe(df_p, use_container_width=True)

# --- TESTIMONIALS PAGE ---
elif page == "Testimonials":
    st.header("💬 Customer Testimonials")
    
    # Loop through the list and add 1 to the loop counter for display
    for i, t in enumerate(testimonials, start=1):
        with st.chat_message("user"):
            # This shows "Testimonial 1" for the item at index 0
            st.write(f"**Testimonial {i}** ({t['author']}): {t['text']}")

# --- REVIEWS PAGE (The Core Feature) ---
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
        # 3. Sentiment Analysis
        with st.spinner('Analyzing sentiment...'):
            results = sentiment_pipeline(filtered_df['text'].tolist())
            filtered_df['Sentiment'] = [r['label'] for r in results]
            filtered_df['Confidence'] = [round(r['score'], 4) for r in results]

        # 4. Visualization: Bar Chart
        st.subheader(f"Sentiment Split for {selected_month_name}")
        sentiment_counts = filtered_df['Sentiment'].value_counts().reset_index()
        avg_confidence = filtered_df.groupby('Sentiment')['Confidence'].mean().reset_index()
        
        # Merging counts and confidence for the tooltip
        viz_df = sentiment_counts.merge(avg_confidence, on='Sentiment')
        
        fig = px.bar(viz_df, x='Sentiment', y='count', 
                     color='Sentiment',
                     hover_data=['Confidence'],
                     labels={'count': 'Number of Reviews', 'Confidence': 'Avg Confidence'},
                     title="Positive vs Negative Counts")
        st.plotly_chart(fig, use_container_width=True)

        # 5. BONUS: Word Cloud (+2 pts)
        st.subheader("Word Cloud")
        text_combined = " ".join(filtered_df['text'].tolist())
        wordcloud = WordCloud(background_color='white', width=800, height=400).generate(text_combined)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        st.pyplot(plt)

        # Show raw filtered data
        st.subheader("Filtered Reviews List")
        st.table(filtered_df[['date', 'text', 'Sentiment', 'Confidence']])