import os
import pandas as pd
import dash
from dash import html, dcc, callback_context
from dash.dependencies import Input, Output
import plotly.express as px

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

df = pd.read_csv(
    "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMDeveloperSkillsNetwork-DV0101EN-SkillsNetwork/Data%20Files/Historical_Wildfires.csv"
)

df["Date"] = pd.to_datetime(df["Date"])
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month_name()

month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)

region_options = [
    {"label": "New South Wales", "value": "NSW"},
    {"label": "Northern Territory", "value": "NT"},
    {"label": "Queensland", "value": "QL"},
    {"label": "South Australia", "value": "SA"},
    {"label": "Tasmania", "value": "TA"},
    {"label": "Victoria", "value": "VI"},
    {"label": "Western Australia", "value": "WA"},
]

card_style = {
    "backgroundColor": "#f9f9f9",
    "padding": "15px",
    "margin": "10px",
    "borderRadius": "12px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
    "textAlign": "center",
    "flex": "1",
    "minWidth": "200px"
}

graph_container_style = {
    "backgroundColor": "white",
    "padding": "10px",
    "margin": "10px",
    "borderRadius": "12px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
    "flex": "1",
    "minWidth": "450px"
}

year_min = int(df["Year"].min())
year_max = int(df["Year"].max())

app.layout = html.Div(
    style={"backgroundColor": "#f4f6f9", "padding": "20px"},
    children=[
        html.H1(
            "Australia Wildfire Dashboard",
            style={
                "textAlign": "center",
                "color": "#503D36",
                "fontSize": "34px",
                "marginBottom": "30px"
            }
        ),

        html.Div(
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "justifyContent": "space-between",
                "gap": "20px",
                "marginBottom": "20px"
            },
            children=[
                html.Div(
                    style={"flex": "2", "minWidth": "300px"},
                    children=[
                        html.H3("Select Region"),
                        dcc.RadioItems(
                            options=region_options,
                            value="NSW",
                            id="region",
                            inline=True
                        )
                    ]
                ),
                html.Div(
                    style={"flex": "1", "minWidth": "300px"},
                    children=[
                        html.H3("Select Year"),
                        dcc.Slider(
                            min=year_min,
                            max=year_max,
                            step=1,
                            value=2005,
                            marks={year: str(year) for year in range(year_min, year_max + 1)},
                            id="year",
                            tooltip={"placement": "bottom", "always_visible": False}
                        )
                    ]
                )
            ]
        ),

        html.Div(
            id="kpi-cards",
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "justifyContent": "space-between"
            }
        ),

        html.Div(
            style={"display": "flex", "flexWrap": "wrap"},
            children=[
                html.Div(id="plot1", style=graph_container_style),
                html.Div(
                    dcc.Graph(id="plot2-graph"),
                    style=graph_container_style
                ),
            ]
        ),

        html.Div(
            style={"display": "flex", "flexWrap": "wrap"},
            children=[
                html.Div(id="plot3", style=graph_container_style),
                html.Div(id="plot4", style=graph_container_style),
            ]
        )
    ]
)

@app.callback(
    Output("year", "value"),
    [
        Input("plot2-graph", "clickData"),
        Input("year", "value"),
    ]
)
def update_year_from_plot(click_data, slider_year):
    ctx = callback_context

    if not ctx.triggered:
        return slider_year

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "plot2-graph" and click_data:
        return int(click_data["points"][0]["x"])

    return slider_year

@app.callback(
    [
        Output("kpi-cards", "children"),
        Output("plot1", "children"),
        Output("plot2-graph", "figure"),
        Output("plot3", "children"),
        Output("plot4", "children"),
    ],
    [
        Input("region", "value"),
        Input("year", "value"),
    ]
)
def update_dashboard(selected_region, selected_year):
    region_data = df[df["Region"] == selected_region].copy()
    year_region_data = region_data[region_data["Year"] == selected_year].copy()

    total_fire_area = year_region_data["Estimated_fire_area"].sum()
    total_fire_count = year_region_data["Count"].sum()
    avg_radiative_power = year_region_data["Mean_estimated_fire_radiative_power"].mean()
    avg_brightness = year_region_data["Mean_estimated_fire_brightness"].mean()

    monthly_fire_area = (
        year_region_data.groupby("Month", observed=False)["Estimated_fire_area"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    kpis = [
        html.Div([
            html.H4("Total Fire Area"),
            html.H2(f"{total_fire_area:,.1f}", style={"color": "#C0392B"})
        ], style=card_style),

        html.Div([
            html.H4("Total Fire Count"),
            html.H2(f"{total_fire_count:,.0f}", style={"color": "#2E86C1"})
        ], style=card_style),

        html.Div([
            html.H4("Avg Radiative Power"),
            html.H2(f"{avg_radiative_power:,.1f}", style={"color": "#7D3C98"})
        ], style=card_style),

        html.Div([
            html.H4("Avg Brightness"),
            html.H2(f"{avg_brightness:,.1f}", style={"color": "#AF601A"})
        ], style=card_style),
    ]

    fig1 = px.line(
        monthly_fire_area,
        x="Month",
        y="Estimated_fire_area",
        markers=True,
        title=f"{selected_region}: Monthly Fire Area in {selected_year}"
    )
    fig1.update_layout(
        xaxis_title="Month",
        yaxis_title="Estimated Fire Area"
    )

    yearly_count = (
        region_data.groupby("Year", observed=False)["Count"]
        .sum()
        .reset_index()
        .sort_values("Year")
    )

    fig2 = px.line(
        yearly_count,
        x="Year",
        y="Count",
        markers=True,
        title=f"{selected_region}: Total Fire Count Over Years"
    )
    fig2.update_layout(
        xaxis_title="Year",
        yaxis_title="Total Fire Count"
    )

    structure_data = (
        year_region_data.groupby("Month", observed=False)[["Estimated_fire_area", "Count"]]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    fig3 = px.bar(
        structure_data,
        x="Month",
        y=["Estimated_fire_area", "Count"],
        barmode="group",
        title=f"{selected_region}: Fire Structure in {selected_year}",
        labels={
            "value": "Value",
            "variable": "Metric",
            "Month": "Month"
        }
    )
    fig3.update_layout(
        xaxis_title="Month",
        yaxis_title="Value",
        legend_title="Metric"
    )

    scatter_data = (
        year_region_data.groupby("Month", observed=False)[
            ["Mean_estimated_fire_brightness", "Mean_estimated_fire_radiative_power", "Estimated_fire_area", "Count"]
        ]
        .mean()
        .reset_index()
        .sort_values("Month")
    )

    fig4 = px.scatter(
        scatter_data,
        x="Mean_estimated_fire_brightness",
        y="Mean_estimated_fire_radiative_power",
        size="Estimated_fire_area",
        color="Month",
        hover_name="Month",
        hover_data={"Count": ":.1f"},
        title=f"{selected_region}: Brightness vs Radiative Power ({selected_year})",
        labels={
            "Mean_estimated_fire_brightness": "Mean Fire Brightness",
            "Mean_estimated_fire_radiative_power": "Mean Radiative Power",
            "Estimated_fire_area": "Estimated Fire Area",
            "Count": "Mean Fire Count"
        }
    )
    fig4.update_layout(
        xaxis_title="Mean Fire Brightness",
        yaxis_title="Mean Radiative Power"
    )

    return (
        kpis,
        dcc.Graph(figure=fig1),
        fig2,
        dcc.Graph(figure=fig3),
        dcc.Graph(figure=fig4),
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port)
