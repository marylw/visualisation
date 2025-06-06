import plotly.express as px
from dash import Dash, dcc, html

from peaks_scatter import categorical_scatter, scatter, bar
 # or any Plotly Express function e.g. px.bar(...)
# fig.add_trace( ... )
# fig.update_layout( ... )



app = Dash()
app.layout = html.Div([
    dcc.Graph(figure=categorical_scatter, id='categorical-scatter'),
    dcc.Graph(figure=scatter, id='scatter-plot'),
    dcc.Graph(figure=bar, id='bar-plot')
])

app.run_server(debug=True, use_reloader=True)  # Turn off reloader if inside Jupyter