import marimo

__generated_with = "0.1.39"
app = marimo.App(width="full")


@app.cell
def __(network):
    network
    return


@app.cell
def __(city, mo, state):
    mo.hstack([state,city],justify="start")
    return


@app.cell
def __(mo, starttime, stoptime, timezone):
    mo.hstack([starttime,stoptime,timezone],justify="start")
    return


@app.cell
def __(mo):
    clock_preview = mo.ui.switch(label="Show clock preview")
    clock_preview
    return clock_preview,


@app.cell
def __(clock):
    clock
    return


@app.cell
def __(classes, fields, interval, loads, mo):
    mo.vstack([mo.hstack([classes,fields,interval],justify='start'),loads])
    return


@app.cell
def __(mo):
    recorder_preview = mo.ui.switch(label="Show recorder preview")
    recorder_preview
    return recorder_preview,


@app.cell
def __(recorders):
    recorders
    return


@app.cell
def __(mo, start, start_command):
    if start_command:
        _start = mo.vstack([
            mo.md("Ready to start simulation using command"),
            mo.md(f"`{start_command}`"),
            start,
            ])
    else:
        _start = mo.md("Simulation is not ready to start")
    _start
    return


@app.cell
def __(mo):
    _views = ["Table","Graph","Map"]
    results_preview = mo.ui.radio(_views,value="Table",label="Preview results as")
    results_preview
    return results_preview,


@app.cell
def __(results):
    results
    return


@app.cell
def __(alt, dt, mo, outputs, pd, results_preview):
    _tabs = {}
    if results_preview.value == "Table":
        for file in outputs:
            _tabs[file] = mo.ui.table(pd.read_csv(file), pagination=True, page_size=10)
    elif results_preview.value == "Graph":
        for file in outputs:
            _data = pd.read_csv(file,converters={"timestamp":lambda x:dt.datetime.strptime(x,"%Y-%m-%d %H:%M:%S %Z")})
            _chart = alt.Chart(_data).mark_point().encode(
                    x = _data.columns[0],
                    y = _data.columns[1],
                )
            _tabs[file] = mo.ui.altair_chart(_chart)
    if _tabs:
        results = mo.tabs(_tabs)
    else:
        results = mo.md("No results to display")

    return file, results


@app.cell
def __(gridlabd, mo):
    #
    #  networks
    #
    _networks = gridlabd("model","index")
    network = mo.ui.dropdown(options=_networks,label="Model")
    return network,


@app.cell
def __(gridlabd, network):
    #
    # Download model
    #
    if network.value:
        gridlabd("model","get",network.value)
    return


@app.cell
def __(gridlabd, mo):
    #
    # Identify available states
    #
    _states = sorted(set([x[0:2] for x in gridlabd("weather","index")]))
    state = mo.ui.dropdown(options=_states,label="State")
    return state,


@app.cell
def __(gridlabd, mo, re, state):
    #
    # Identify available cities
    #
    if state.value:
        _cities = sorted(set([x[3:] for x in gridlabd("weather","index",f"^{state.value}-")]))
    else:
        _cities = []
    city = mo.ui.dropdown(options=dict([(re.sub("[^A-Za-z]"," ",x.replace(".tmy3","")),x) for x in _cities]),label="City")
    return city,


@app.cell
def __(city, dt, gridlabd, io, mo, pd):
    #
    # Set the clock
    #
    if city.value:
        gridlabd("weather","get",city.value)
        _info = pd.read_csv(io.StringIO("\n".join(gridlabd("weather","info",city.value))))
        _locale = gridlabd("timezone",f"{_info.iloc[0]['Latitude']},{_info.iloc[0]['Longitude']}")[0]
    else:
        _locale = ""
    timezone = mo.ui.text(value=_locale,label="Timezone",placeholder="Enter timezone")
    starttime = mo.ui.date(start="2000-01-01",stop="2999-12-31",value=f"{dt.datetime.now().year}-01-01",label="Start date")
    stoptime = mo.ui.date(start="2000-01-01",stop="2999-12-31",value=f"{dt.datetime.now().year+1}-01-01",label="Stop date")
    return starttime, stoptime, timezone


@app.cell
def __(clock_preview, mo, starttime, stoptime, timezone):
    #
    # Get clock information
    #
    _clock = f"""clock {{
        timezone "{timezone.value}";
        starttime "{starttime.value} 00:00:00";
        stoptime "{stoptime.value} 00:00:00";
    }}
    """
    clock = mo.ui.text_area(value=_clock,full_width=True,label="Clock preview") if clock_preview.value else mo.md("")
    return clock,


@app.cell
def __(city, gridlabd, json, network, os, state, timezone):
    #
    # Compile the model
    #
    model = None
    if network.value and state.value and city.value and timezone.value:
        glmfile = f"{os.path.basename(network.value)}.glm"
        jsonfile = f"{os.path.basename(network.value)}.json"
        gridlabd("-C",glmfile,"-o",jsonfile)
        with open(jsonfile,"r") as fh:
            model = json.load(fh)
            assert(model["application"]=="gridlabd")
            assert(model["version"]>="4.3.3")

    return fh, glmfile, jsonfile, model


@app.cell
def __(classes, mo, model, pd):
    #
    # Identify available objects and fields to records
    #
    if model:
        _loads = pd.DataFrame(dict([(obj,data) for obj,data in model["objects"].items() if data["class"] in classes.value])).transpose().sort_index()
        _loads.drop(axis=1,labels=list(model["header"]),errors='ignore',inplace=True)
        loads = mo.ui.table(data=_loads,label="Objects to record",page_size=5,pagination=True)
        fields = mo.ui.multiselect(sorted(_loads.columns),label="Fields to record")
        interval = mo.ui.dropdown("1s 10s 1min 5min 15min 1h".split(),label="Sampling interval",value="1h")
    else:
        loads = fields = interval = mo.md("")
    return fields, interval, loads


@app.cell
def __(mo, model):
    #
    # Identify available classes to record
    #
    _classes = sorted(model["classes"]) if model else []
    classes = mo.ui.multiselect(options=_classes,label="Classes to record")
    return classes,


@app.cell
def __(fields, interval, loads, mo, recorder_preview):
    #
    # Generate recorders
    #
    _recorders = """module tape {
        csv_header_type NAME;
    }
    """
    if hasattr(loads,"value") and fields.value:
        for name in loads.value.index:
            _recorders += f"""object recorder {{
            parent "{name}";
            property "{','.join(fields.value)}";
            interval "{interval.value}";
            file "{name}.csv";
        }}
        """
    recorders = mo.ui.text_area(value=_recorders,full_width=True,label="Recorders") if recorder_preview.value else mo.md("")
    return name, recorders


@app.cell
def __(clock, glmfile, loads, mo, model, os, recorders):
    #
    # Run the simulation
    #
    _start = None

    def _stop(x):
        mo.ui.button(label="Start",on_click=_start)

    def _start(x):
        start = mo.ui.button(label="Stop",on_click=_stop)
        with open("recorders.glm","w") as fh:
            fh.write(recorders.value)
        with open("clock.glm","w") as fh:
            fh.write(clock.value)
        with mo.redirect_stderr():
            with mo.redirect_stdout():
                os.system(start_command)
        mo.ui.button(label="Start",on_click=_start)

    if model:# and clock.value and recorders.value:
        start_command = f"gridlabd {glmfile} clock.glm recorders.glm -D keep_progress=TRUE"
        outputs = [f"{x}.csv" for x in loads.value.index]
    else:
        start_command = ""
        outputs = []

    start = mo.ui.button(label="Start",on_click=_start,disabled=False if model else True)
    return outputs, start, start_command


@app.cell
def __(sp, sys):
    def gridlabd(*args,**kwargs):
        """Run gridlabd
        Arguments:
        - *args: command arguments
        - **kwargs: global definitions (placed before command arguments)
        """
        cmd = ["gridlabd"]
        for name,value in kwargs.items():
            cmd.extend(["-D", f"{name}={value}"])
        cmd.extend(args)
        print(f"[Running '{' '.join(cmd)}']",file=sys.stdout)
        # with mo.status.spinner(f"Running command '{cmd}'"):
        r = sp.run(cmd,capture_output=True,text=True)
        print(r.stderr,file=sys.stderr)
        if r.returncode != 0:
            raise Exception(f"gridlabd error code {r.returncode}")
        return r.stdout.strip().split("\n")
    return gridlabd,


@app.cell
def __():
    import os, sys, re, io, json
    import datetime as dt
    import marimo as mo
    import subprocess as sp
    import pandas as pd
    import altair as alt
    return alt, dt, io, json, mo, os, pd, re, sp, sys


if __name__ == "__main__":
    app.run()
