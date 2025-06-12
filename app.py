import plotly.express as px
from dash import Dash, dcc, html

from peaks_scatter import categorical_scatter, scatter, bar
from map import static_hotspot_map, mobile_hotspot_map



app = Dash()
app.layout = html.Div([
    dcc.Graph(figure=categorical_scatter, id='categorical-scatter'),
    dcc.Graph(figure=scatter, id='scatter-plot'),
    dcc.Graph(figure=bar, id='bar-plot'),
    dcc.Graph(figure=static_hotspot_map, id='statichotspot'),
    dcc.Graph(figure=mobile_hotspot_map, id='mobilehotspot')
])

app.run(debug=True, use_reloader=True)  # Turn off reloader if inside Jupyter