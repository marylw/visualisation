import plotly.express as px
from dash import Dash, dcc, html

from peaks_scatter import categorical_scatter, scatter, bar



app = Dash()
app.layout = html.Div([
    dcc.Graph(figure=categorical_scatter, id='categorical-scatter'),
    dcc.Graph(figure=scatter, id='scatter-plot'),
    dcc.Graph(figure=bar, id='bar-plot')
])

app.run(debug=True, use_reloader=True)  # Turn off reloader if inside Jupyter