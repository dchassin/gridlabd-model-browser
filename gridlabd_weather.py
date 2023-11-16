import marimo

__generated_with = "0.1.50"
app = marimo.App(width="full")


@app.cell
def __(gridlabd, mo):
    gridlabd_version = gridlabd("--version=all", binary=True)
    mo.md(gridlabd_version)
    return gridlabd_version,


@app.cell
def __(io, mo, pd):
    get_data,set_data = mo.state(None)
    get_fields, set_fields = mo.state(mo.md(""))

    def preview(_):
        data = io.StringIO(
            "x,y\n0,1.23\n1,2.34\n2,3.45" # test data
            # gridlabd("nsrdb_weather",
            #             f"-y={year.value}",
            #             f"-p={latitude.value},{longitude.value}")
        )
        df = pd.read_csv(data,parse_dates=True,index_col=None)
        set_data(df)
        fields = list(df.columns)
        print(fields)
        # set_fields(mo.md("") if get_data() is None else mo.hstack([
        #     mo.ui.dropdown(fields,label="Horizontal axis:"),
        #     mo.ui.multiselect(fields,label="Vertical axis:"),
        # ],justify='start'))
        
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
def __(get_fields):
    get_fields()
    return


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
def __(os, sp, sys):
    last_stderr = None

    def gridlabd(*args, binary=False, split=None,**kwargs):
        """Run gridlabd
        Arguments:
        - *args: command arguments
        - **kwargs: global definitions (placed before command arguments)
        """
        cmd = [
            "gridlabd.bin" if binary and "GLD_BIN" in os.environ else "gridlabd"
        ]
        for name, value in kwargs.items():
            cmd.extend(["-D", f"{name}={value}"])
        cmd.extend(args)
        print(f"[Running '{' '.join(cmd)}']",file=sys.stdout)
        # with mo.status.spinner(f"Running command '{cmd}'"):
        global last_stderr
        last_stderr = None
        r = sp.run(cmd, capture_output=True, text=True)
        last_stderr = r.stderr
        if r.returncode != 0:
            raise Exception(f"gridlabd error code {r.returncode}")
        print(f"[{len(r.stdout)} bytes received]",file=sys.stdout)
        return r.stdout.strip().split(split if type(split) is str else "\n") if split else r.stdout
    return gridlabd, last_stderr


@app.cell
def __():
    import marimo as mo
    import os, sys, io
    import subprocess as sp
    import pandas as pd
    return io, mo, os, pd, sp, sys


if __name__ == "__main__":
    app.run()
