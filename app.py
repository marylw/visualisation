import plotly.express as px
from dash import Dash, dcc, html, Input, Output

from peaks_scatter import (
    gdf_joined_static, gdf_joined_mobile, gdf_joined_combined,
    combined_peak_plot, peaks
)
from map import static_hotspot_map, mobile_hotspot_map

app = Dash()
app.layout = html.Div([
    html.Label("Select Data Source:"),
    dcc.Dropdown(
        id='data-source',
        options=[
            {'label': 'Combined Sensors', 'value': 'combined'},
            {'label': 'Static Sensors', 'value': 'static'},
            {'label': 'Mobile Sensors', 'value': 'mobile'},
        ],
        value='combined'
    ),
    dcc.Graph(id='categorical-scatter'),
    dcc.Graph(id='scatter-plot'),
    dcc.Graph(id='bar-plot'),
    dcc.Graph(id='statichotspot'),
    dcc.Graph(id='mobilehotspot')
])

@app.callback(
    Output('categorical-scatter', 'figure'),
    Output('scatter-plot', 'figure'),
    Output('bar-plot', 'figure'),
    Output('statichotspot', 'figure'),
    Output('mobilehotspot', 'figure'),
    Input('data-source', 'value')
)
def update_plots(source):
    if source == 'static':
        df = gdf_joined_static
        static_map = static_hotspot_map
        mobile_map = {}
    elif source == 'mobile':
        df = gdf_joined_mobile
        static_map = {}
        mobile_map = mobile_hotspot_map
    else:
        df = gdf_joined_combined
        static_map = static_hotspot_map
        mobile_map = mobile_hotspot_map

    scatter_fig, bar_fig = combined_peak_plot(df, combined=False)
    normalized_df = peaks(df)
    categorical_scatter = px.scatter(normalized_df, y="Nbrhood", x="Timestamp")
    categorical_scatter.update_layout(
        title='Peaks per Neighborhood',
        xaxis_title='Time',
        yaxis_title='Neighborhood',
    )
    return categorical_scatter, scatter_fig, bar_fig, static_map, mobile_map

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)