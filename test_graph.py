import marimo

__generated_with = "0.1.50"
app = marimo.App()


@app.cell
def __(io, mo, pd):
    get_data,set_data = mo.state(None)
    get_fields, set_fields = mo.state(mo.md(""))

    def preview(_):
        data = io.StringIO("index,value\n0,A\n1,B\n2,C"
            # gridlabd("nsrdb_weather",
            #             f"-y={year.value}",
            #             f"-p={latitude.value},{longitude.value}")
        )
        df = pd.read_csv(data,parse_dates=True,index_col=None)
        set_data(df)
        fields = list(df.columns)
        set_fields(mo.md("") if get_data() is None else mo.hstack([
            mo.ui.dropdown(fields,label="Horizontal axis:"),
            mo.ui.multiselect(fields,label="Vertical axis:"),
        ],justify='start'))
        
    def get_table():
        data = get_data()
        if data is None:
            return
        return mo.ui.table(get_data(), page_size=24)

    def get_graph():
        data = get_data()
        if data is None:
            return
        return mo.vstack([
            get_fields(),
            get_data().plot()
        ])

    year = mo.ui.number(start=2000,stop=2020,label="Year:",value=2020)
    latitude = mo.ui.text(label="Latitude:",value="37.5")
    longitude = mo.ui.text(label="Longitude:",value="-122.3")
    show = mo.ui.button(label="Refresh",on_click=preview)
    return (
        get_data,
        get_fields,
        get_graph,
        get_table,
        latitude,
        longitude,
        preview,
        set_data,
        set_fields,
        show,
        year,
    )


@app.cell
def __(get_graph, get_table, latitude, longitude, mo, show, year):
    mo.vstack([
        mo.hstack([latitude,longitude,year,show]),
        mo.tabs({
            "Table":get_table(),
            "Graph":get_graph(),
        }),
    ])
    return


@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import io
    return io, mo, pd


if __name__ == "__main__":
    app.run()
