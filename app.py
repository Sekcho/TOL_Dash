from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import os

# Function to preprocess dataset
def preprocess_dataset(file_path):
    data = pd.read_csv(file_path)

    # Convert market share columns to percentages
    market_share_columns = [
        "Market Share True (%)",
        "Market Share AIS (%)",
        "Market Share 3BB (%)",
        "Market Share NT (%)"
    ]
    for col in market_share_columns:
        data[col] = (data[col] * 100).round(2)  # Convert to percentage

    return data

# Load Dataset
file_path = os.path.join(os.path.dirname(__file__), 'Prepared_True_Dataset.csv')  # Use dynamic path
data = preprocess_dataset(file_path)

# Create Dash App
app = Dash(__name__)
server = app.server

# Layout
app.layout = html.Div([
    html.H1("TOL Sales Potential and Market Share Insights for South", style={'textAlign': 'center'}),

    # Filters
    html.Div([
        html.Label("Select Province:"),
        dcc.Dropdown(
            id='province-filter',
            options=[{'label': province, 'value': province} for province in data['Province'].unique()],
            placeholder="Select Province",
        ),
        html.Label("Select District:"),
        dcc.Dropdown(
            id='district-filter',
            placeholder="Select District",
        ),
        html.Label("Select Sub-district:"),
        dcc.Dropdown(
            id='subdistrict-filter',
            placeholder="Select Sub-district",
        ),
        html.Label("Select Happy Block:"),
        dcc.Dropdown(
            id='happyblock-filter',
            placeholder="Select Happy Block",
        ),
        html.Label("Net Add Filter:"),
        dcc.RangeSlider(
            id='net-add-slider',
            min=int(data['Net Add'].min()),
            max=int(data['Net Add'].max()),
            step=2,
            marks={i: str(i) for i in range(int(data['Net Add'].min()), int(data['Net Add'].max()) + 1, 2)},
            value=[int(data['Net Add'].min()), int(data['Net Add'].max())]
        ),
        html.Label("Potential Score Range:"),
        dcc.RangeSlider(
            id='potential-score-slider',
            min=0, max=100, step=1,
            marks={i: f"{i}%" for i in range(0, 101, 10)},
            value=[0, 100]
        ),
        html.Label("Market Share True (%) Range:"),
        dcc.RangeSlider(
            id='market-share-true-slider',
            min=0, max=100, step=1,
            marks={i: str(i) for i in range(0, 101, 10)},
            value=[0, 100]
        ),
    ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),

    # Map Display
    dcc.Graph(
        id='map',
        style={'width': '65%', 'display': 'inline-block'},
        config={'scrollZoom': True}  # Enable scroll zoom
    )
])

# Callbacks for Filters
@app.callback(
    Output('district-filter', 'options'),
    Input('province-filter', 'value')
)
def update_district_filter(selected_province):
    if selected_province:
        filtered = data[data['Province'] == selected_province]
        return [{'label': district, 'value': district} for district in filtered['District'].unique()]
    return []

@app.callback(
    Output('subdistrict-filter', 'options'),
    [Input('province-filter', 'value'),
     Input('district-filter', 'value')]
)
def update_subdistrict_filter(selected_province, selected_district):
    filtered = data.copy()
    if selected_province:
        filtered = filtered[filtered['Province'] == selected_province]
    if selected_district:
        filtered = filtered[filtered['District'] == selected_district]
    return [{'label': subdistrict, 'value': subdistrict} for subdistrict in filtered['Sub-district'].unique()]

@app.callback(
    Output('happyblock-filter', 'options'),
    [Input('province-filter', 'value'),
     Input('district-filter', 'value'),
     Input('subdistrict-filter', 'value')]
)
def update_happyblock_filter(selected_province, selected_district, selected_subdistrict):
    filtered = data.copy()
    if selected_province:
        filtered = filtered[filtered['Province'] == selected_province]
    if selected_district:
        filtered = filtered[filtered['District'] == selected_district]
    if selected_subdistrict:
        filtered = filtered[filtered['Sub-district'] == selected_subdistrict]
    return [{'label': happy_block, 'value': happy_block} for happy_block in filtered['Happy Block'].unique()]

@app.callback(
    Output('map', 'figure'),
    [Input('province-filter', 'value'),
     Input('district-filter', 'value'),
     Input('subdistrict-filter', 'value'),
     Input('happyblock-filter', 'value'),
     Input('net-add-slider', 'value'),
     Input('potential-score-slider', 'value'),
     Input('market-share-true-slider', 'value')]
)
def update_map(selected_province, selected_district, selected_subdistrict, selected_happyblock,
               net_add_range, potential_range, market_share_range):
    # Filter Data
    filtered_data = data.copy()
    if selected_province:
        filtered_data = filtered_data[filtered_data['Province'] == selected_province]
    if selected_district:
        filtered_data = filtered_data[filtered_data['District'] == selected_district]
    if selected_subdistrict:
        filtered_data = filtered_data[filtered_data['Sub-district'] == selected_subdistrict]
    if selected_happyblock:
        filtered_data = filtered_data[filtered_data['Happy Block'] == selected_happyblock]
    filtered_data = filtered_data[
        (filtered_data['Net Add'] >= net_add_range[0]) &
        (filtered_data['Net Add'] <= net_add_range[1]) &
        (filtered_data['Potential Score'] >= potential_range[0]) &
        (filtered_data['Potential Score'] <= potential_range[1]) &
        (filtered_data['Market Share True (%)'] >= market_share_range[0]) &
        (filtered_data['Market Share True (%)'] <= market_share_range[1])
    ]

    # Create Map
    fig = px.scatter_mapbox(
        filtered_data,
        lat="Latitude",
        lon="Longitude",
        size="Port Use",  # Changed from Household to Port Use
        color="Potential Score",
        hover_name="Sub-district",
        hover_data={
            "Province": True,
            "District": True,
            "Sub-district": True,
            "Happy Block": True,
            "Market Share AIS (%)": True,
            "Market Share 3BB (%)": True,
            "Market Share NT (%)": True,
            "Market Share True (%)": True,
            "Install": True,
            "Net Add": True,
        },
        color_continuous_scale=["red", "green"],
        title="Potential Score and Market Share Map",
        mapbox_style="open-street-map",
        zoom=9
    )

    fig.update_layout(
        mapbox={
            "style": "open-street-map",
            "zoom": 9,
            "center": {"lat": filtered_data["Latitude"].mean(), "lon": filtered_data["Longitude"].mean()}
        },
        uirevision='constant',
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    return fig

# Run App
if __name__ == '__main__':
    app.run_server(debug=True)
