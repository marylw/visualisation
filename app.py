import plotly.express as px
from dash import Dash, dcc, html, Input, Output

from peaks_scatter import (
    gdf_joined_static, gdf_joined_mobile, gdf_joined_combined,
    combined_peak_plot, peaks
)
from map import static_hotspot_map, mobile_hotspot_map
from advice import df_decisions

dates = df_decisions['Day of Interest'].unique()
# Create the dashboard
app = Dash()
app.layout = html.Div([
    html.Label("Select Sensors:"),
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
    dcc.Graph(id='scatter-plot', style={'width': '60%', 'display': 'inline-block'}),
    html.Div([
        html.Label("Select Day for Advice Summary"),
        dcc.Dropdown(
            id='day-dropdown',
            options=[{'label': d, 'value': d} for d in dates],
            value=dates[0],
            style={'margin-bottom': '10px'}
        ),
        html.Div(id='decision-output')
    ], style={'width': '38%', 'verticalAlign': 'top', 'display': 'inline-block', 'paddingLeft': '2%'}),
    dcc.Graph(id='bar-plot'),
    dcc.Graph(id='statichotspot', style={'width': '48%', 'display': 'inline-block'}),
    dcc.Graph(id='mobilehotspot', style={'width': '48%', 'display': 'inline-block'})
    ])

@app.callback(
    Output('categorical-scatter', 'figure'),
    Output('scatter-plot', 'figure'),
    Output('bar-plot', 'figure'),
    Output('statichotspot', 'figure'),
    Output('mobilehotspot', 'figure'),
    Output('decision-output', 'children'),
    Input('data-source', 'value'),
    Input('day-dropdown', 'value')
)

# Show correct plots based on selected sensors
def update_plots(source, selected_day):
    import plotly.graph_objects as go
    empty_fig = go.Figure()

    if source == 'static':
        df = gdf_joined_static
        static_map = static_hotspot_map
        mobile_map = empty_fig
    elif source == 'mobile':
        df = gdf_joined_mobile
        static_map = empty_fig
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
    
    decision_text = update_decision_text(selected_day)
    return categorical_scatter, scatter_fig, bar_fig, static_map, mobile_map, decision_text

# Ensure the advice is nicely formatted
def update_decision_text(selected_day):
    row = df_decisions[df_decisions['Day of Interest'].astype(str) == selected_day]
    if row.empty:
        return "No information for this day."
    row = row.iloc[0]

    # Format lists
    cleaning = ", ".join(row['Cleaning'])
    decontam = ", ".join(row['Decontamination Citizens'])
    shelter = ", ".join(row['Shelter'])

    # Format sensor recommendations as a table
    sensor_recs = row['Sensor Recommendations']
    table_header = [html.Tr([html.Th("Neighborhood"), html.Th("Sensor Type")])]
    table_body = [html.Tr([html.Td(n), html.Td(t)]) for n, t in sensor_recs]
    sensor_table = html.Table(table_header + table_body, style={'border': '1px solid black', 'margin-top': '10px'})

    return html.Div([
        html.P(f"Cleaning and Inspection Area: {cleaning}"),
        html.P(f"Decontamination Citizens: {decontam}"),
        html.P(f"Shelter: {shelter}"),
        html.P("Sensor Recommendations:"),
        sensor_table
    ])

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)