import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from pybaseball import statcast
from pybaseball import statcast_pitcher

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

pitchers = pd.read_csv('pitchersnew.csv')
pitchers.sort_values(by='name_first',inplace=True)
left_pitchers = pitchers.loc[pitchers['hand'] == 'L']
right_pitchers = pitchers.loc[pitchers['hand'] == 'R']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='Statcast Pitcher Velocity Distribution'),
    html.Label('LHP'),
    dcc.Dropdown(id='leftdropdown', 
        options=[
            {'label': i, 'value': i} for i in left_pitchers.Name.unique()
        ],),
    html.Label('RHP'),
    dcc.Dropdown(id='rightdropdown',
        options=[
            {'label': i, 'value': i} for i in right_pitchers.Name.unique()
        ],) ,
    dcc.Graph(id='graph'),
    dcc.Slider(
        id='slider',
        min = 2008,
        max = 2021,
        value = 5,
        marks = {i: 'Label {}'.format(i) if i == 1 else str(i) for i in range(2008, 2022)}
    )
])

@app.callback(
    Output('rightdropdown','disabled'),
    Output('leftdropdown','disabled'),
    Input('leftdropdown','value'),
    Input('rightdropdown','value')
)
def set_options(leftselection, rightselection):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == 'leftdropdown':
        if leftselection != None:
            return True, False
    if trigger_id == 'rightdropdown':
        if rightselection != None:
            return False, True
    return False, False

@app.callback(
    [Output('slider','min'),
    Output('slider', 'max')],
    Input('leftdropdown','value'),
    Input('rightdropdown', 'value')
)
def populate_slider(left_pitcher, right_pitcher):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == 'leftdropdown':
        selected_pitcher = left_pitcher
    if trigger_id == 'rightdropdown':
        selected_pitcher = right_pitcher
    mins = list(pitchers.loc[pitchers['Name'] == selected_pitcher]['mlb_played_first'])[0]
    if mins < 2008:
        mins = 2008
    maxs = list(pitchers.loc[pitchers['Name'] == selected_pitcher]['mlb_played_last'])[0]
    return mins, maxs   

@app.callback(
    Output('graph','figure'),
    Input('leftdropdown','value'),
    Input('rightdropdown','value'),
    Input('slider','value')
)
def update_figure(left_pitcher, right_pitcher, selected_year):
    if left_pitcher == None:
        selected_pitcher = right_pitcher
    else:
        selected_pitcher = left_pitcher
    key = list(pitchers.loc[pitchers['Name'] == selected_pitcher]['key_mlbam'])[0]
    dat = statcast_pitcher(f'{selected_year}-01-01', f'{selected_year}-12-31', key)[['pitch_type','release_speed', 'pitch_name']]
    dat = dat.dropna()
    dat = dat[(dat.pitch_name != 'Pitch Out') & (dat.pitch_name != 'Intentional Ball') ]
    fig = px.histogram(dat, x='release_speed', color='pitch_name', barmode='overlay',
                labels={
                    "release_speed": "Pitch Speed",
                    "pitch_name": "Pitch Type"}, 
                   title=f'{selected_pitcher} Frequency of Pitch Arsenal by Pitch Speed In {selected_year}')
    return fig

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

if __name__ == '__main__':
    app.run_server(debug=True)