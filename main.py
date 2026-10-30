import pandas as pd
import ast
import plotly.express as px
import plotly.io as pio
from pathlib import Path
from string import Template

# ---------------------------------------------------
# Data Cleaning Process
# ---------------------------------------------------
# Creating a Pandas DataFrame
file_path = 'data/metacritic-steam.csv'
df = pd.read_csv(file_path)

# Creating Average Metacritic Score by Year DataFrame
df_yearscore = df.groupby('year', as_index=False).agg(
    {'metacritic_score':'mean'}
)

# Creating Preço x Metacritic Score DataFrame
columns = ['name','price','metacritic_score','year']
df_pricescore = df[columns].copy()
df_pricescore

# Converting Genres column, transforming from text to python lists
# Normalizing values to avoid empty or duplicated categories
def convert_genres(value):
    if pd.isna(value): return []

    if isinstance(value, list): genres = value
    
    else:
        try:
            genres = ast.literal_eval(value)
        except (ValueError, SyntaxError, TypeError):
            return []

    # Ensures that the result is always a list
    if isinstance(genres, str):
        genres = [genres]

    if not isinstance(genres, (list, tuple, set)):
        return []

    # Remove extra spaces, blank values, and duplicates per game
    genres = [
        genre.strip()
        for genre in genres
        if isinstance(genre, str) and genre.strip()
    ]

    return list(dict.fromkeys(genres))

# Applying Converting Genres into the main DataFrame
df['genres'] = df['genres'].apply(convert_genres)

# Separating all values from the list without losing the game statistics
df_genres = (
    df
    .explode('genres')
    .dropna(subset=['genres'])
    .copy()
)

# Creating Average Metacritic Score by Genre DataFrame
df_genrescore = df_genres.groupby('genres', as_index=False).agg(
    {'metacritic_score':'mean'}
)
df_genrescore.sort_values(by='metacritic_score',inplace=True)

# Creating sub dataset to count genre positive and negative review
df_genrereview = (
    df_genres
    .groupby('genres', as_index=False).agg(
        {
            'positive':'sum',
            'negative':'sum'
        }
    )
)

# Creating Positive and Negative Reviews by Genre Order
df_genreorder = (
    df_genrereview
    .sort_values('positive', ascending=True)['genres']
    .tolist()
)

# Creating Positive and Negative Reviews by Genre DataFrame
df_genrereview = df_genrereview.melt(
    id_vars='genres',
    value_vars=['positive', 'negative'],
    var_name='review type',
    value_name='quantity'
)

df_genrereview['review type'] = (
    df_genrereview['review type']
)

# ---------------------------------------------------
# Creating Plotly Figures
# ---------------------------------------------------
# Line Chart 
fig_yearscore = px.line(
    df_yearscore,
    x='year',
    y='metacritic_score',
    markers=True,
    title='Average Metacritic Score by Year'
)

# Scatter Plot
fig_pricescore = px.scatter(
    df_pricescore,
    x='price',
    y='metacritic_score',
    hover_name='name',
    hover_data=['year'],
    title='Relationship Between Game Price and Metacritic Score'
)

# Horizontal Bar Chart
fig_genrescore = px.bar(
    df_genrescore,
    y='genres',
    x='metacritic_score',
    title='Average Metacritic Score by Genre',
    orientation='h'
)

# Stacked Horizontal Bar Chart  
fig_genrereview = px.bar(
    df_genrereview,
    x='quantity',
    y='genres',
    color='review type',
    title='Positive and Negative Reviews by Genre',
    orientation='h',
    barmode='stack'
)

fig_genrereview.update_yaxes(
        categoryorder='array',
        categoryarray=df_genreorder
    )

# ---------------------------------------------------
# Creating Dashboard HTML file
# ---------------------------------------------------
metrics = {
    "Games Analyzed": f"{len(df):,}",
    "Avg. Metacritic Score": f"{df['metacritic_score'].mean():.1f}",
    "Total Unique Genres": f"{df['genres'].explode().dropna().nunique():,}",
    "Total Unique Developers": f"{df['developers'].nunique():,}"
}

cards = "".join(
    f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """
    for label, value in metrics.items()
)

figures = [fig_yearscore, fig_pricescore, fig_genrescore, fig_genrereview]

for fig in figures:
# Apply a consistent theme to all charts
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        font=dict(color="#e2e8f0"),
        margin=dict(l=35, r=25, t=55, b=35),
        height=350
    )

charts = "".join(
    f'<div class="chart-card">{pio.to_html(fig, full_html=False, include_plotlyjs=(i == 0), config={"responsive": True})}</div>'
    for i, fig in enumerate(figures)
)

template = Template(Path("dashboard-html/dashboard_template.html").read_text(encoding="utf-8"))

dashboard = template.substitute(cards=cards, charts=charts)

output = Path("dashboard-html/dashboard.html")
output.write_text(dashboard, encoding="utf-8")

print(f"Dashboard saved to: {output}")