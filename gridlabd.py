import marimo

__generated_with = "0.1.47"
app = marimo.App(width="full")


@app.cell
def __(
    city,
    classes,
    clock,
    fields,
    gridlabd_copyright,
    gridlabd_license,
    gridlabd_version,
    interval,
    loads,
    mo,
    model_stats,
    network,
    recorders,
    results,
    results_preview,
    start_preview,
    starttime,
    state,
    stoptime,
    timezone,
    weather_stats,
):
    mo.vstack([
        mo.md(gridlabd_version[0]),
        mo.md("---"),
        mo.tabs({
            "Network" : mo.vstack([
                network,
                mo.ui.table(model_stats,selection=None) if not model_stats is None else mo.md("No model info")
                ]),
            "Weather" : mo.vstack([
                mo.hstack([state,city],justify="start"),
                mo.ui.table(weather_stats,selection=None) if not weather_stats is None else mo.md("No weather info"),
                ]),
            "Clock" : mo.vstack([
                mo.hstack([starttime,stoptime,timezone],justify="start"),
                clock,
                ]),
            "Output" : mo.vstack([
                mo.vstack([mo.hstack([classes,fields,interval],justify='start'),loads]),
                recorders,
                ]),
            "Results" : mo.vstack([
                start_preview,
                results_preview,
                results,
                ]),
            "Map" : mo.vstack([
                mo.md("No geodata found")
                ]),
            "About" : mo.vstack([
                mo.Html("<BR/>".join(gridlabd_license)),
                ]),
            "Help" : mo.vstack([
                mo.md(f"""<iframe height="800px" width="100%" src="https://docs.gridlabd.us" title="GridLAB-D Documentation"></iframe>"""),
                ]),
            }),
        mo.md("<BR/><BR/><BR/><BR/>"),
        mo.md("---"),
        mo.md("<BR/>".join([x for x in gridlabd_copyright if x.startswith("Copyright")])),
        ])
    return


@app.cell
def __(clock, mo, recorders, start, start_command):
    if start_command and (not hasattr(clock,"value") or clock.value) and (not hasattr(recorders,"value") or recorders.value):
        start_preview = mo.vstack([
            mo.md("Ready to start simulation using command"),
            mo.md(f"`{start_command}`"),
            start,
            ])
    else:
        start_preview = mo.md("Simulation is not ready to start")
    return start_preview,


@app.cell
def __(mo):
    _views = ["Table","Graph"]
    results_preview = mo.ui.radio(_views,value="Table",label="Preview results as")
    return results_preview,


@app.cell
def __(alt, dt, mo, outputs, pd, results_preview):
    _tabs = {}
    for file in outputs:
        try:
            if results_preview.value == "Table":
                _tabs[file] = mo.ui.table(pd.read_csv(file), pagination=True, page_size=10)
            elif results_preview.value == "Graph":
                _data = pd.read_csv(file,converters={"timestamp":lambda x:dt.datetime.strptime(x,"%Y-%m-%d %H:%M:%S %Z")})
                _chart = alt.Chart(_data).mark_point().encode(
                        x = _data.columns[0],
                        y = _data.columns[1],
                    )
                _tabs[file] = mo.ui.altair_chart(_chart)
        except:
            pass
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
    weather_stats = None
    if city.value:
        gridlabd("weather","get",city.value)
        weather_stats = pd.read_csv(io.StringIO("\n".join(gridlabd("weather","info",city.value)))).transpose()
        weather_stats.index.name = "Property"
        weather_stats.columns = ["Value"]
        _locale = gridlabd("timezone",f"{weather_stats.loc['Latitude']['Value']},{weather_stats.loc['Longitude']['Value']}")[0]
    else:
        _locale = ""
    timezone = mo.ui.text(value=_locale,label="Timezone",placeholder="Enter timezone")
    starttime = mo.ui.date(start="2000-01-01",stop="2999-12-31",value=f"{dt.datetime.now().year}-01-01",label="Start date")
    stoptime = mo.ui.date(start="2000-01-01",stop="2999-12-31",value=f"{dt.datetime.now().year+1}-01-01",label="Stop date")
    return starttime, stoptime, timezone, weather_stats


@app.cell
def __(mo, starttime, stoptime, timezone):
    #
    # Get clock information
    #
    _clock = f"""clock {{
        timezone "{timezone.value}";
        starttime "{starttime.value} 00:00:00";
        stoptime "{stoptime.value} 00:00:00";
    }}
    """
    clock = mo.ui.text_area(value=_clock,full_width=True,label="Clock preview")
    return clock,


@app.cell
def __(gridlabd_bin, json, network, os, pd, re):
    #
    # Compile the model
    #
    model = None
    model_stats = None
    if network.value: # and state.value and city.value and timezone.value:
        glmfile = f"{os.path.basename(network.value)}.glm"
        jsonfile = f"{os.path.basename(network.value)}.json"
        gridlabd_bin("-C",glmfile,"-o",jsonfile)
        with open(jsonfile,"r") as fh:
            model = json.load(fh)
            assert(model["application"]=="gridlabd")
            assert(model["version"]>="4.3.3")
            _stats = {}
            for obj,data in model["objects"].items():
                if data["class"] in _stats:
                    _stats[data["class"]] += 1
                else:
                    _stats[data["class"]] = 1
            model_stats = pd.concat([pd.DataFrame([(re.sub("[^A-Za-z0-9]"," ",x).title(),y)]) for x,y in sorted(_stats.items())]).set_index(0)
            model_stats.index.name = "Class Name"
            model_stats.columns = ["Object Count"]
            # model_stats[0] = [x.re("[^A-Za-z0-9"," ").title() for x in models_stats[0]]

    return data, fh, glmfile, jsonfile, model, model_stats, obj


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
def __(fields, interval, loads, mo):
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
    recorders = mo.ui.text_area(value=_recorders,full_width=True,label="Recorders")
    return name, recorders


@app.cell
def __(city, clock, glmfile, loads, mo, model, os, recorders, state):
    #
    # Run the simulation
    #
    _start = None

    def _stop(x):
        mo.ui.button(label="Start",on_click=_start)

    def _start(x):
        start = mo.ui.button(label="Stop",on_click=_stop)
        with open("_recorders.glm","w") as fh:
            fh.write(recorders.value)
        with open("_clock.glm","w") as fh:
            fh.write(clock.value)
        with open("_weather.glm","w") as fh:
            fh.write(f"""module climate;
    #weather get {city.value}
    object climate {{
        tmyfile "${{GLD_ETC}}/weather/US/{state.value}-{city.value}";
    }}
    """)
        with mo.redirect_stderr():
            with mo.redirect_stdout():
                os.system(start_command)
        mo.ui.button(label="Start",on_click=_start)

    if model:# and clock.value and recorders.value:
        start_command = f"gridlabd {glmfile} _weather.glm _clock.glm _recorders.glm -D keep_progress=TRUE"
        outputs = [f"{x}.csv" for x in loads.value.index]
    else:
        start_command = ""
        outputs = []

    start = mo.ui.button(label="Start",on_click=_start,disabled=False if model else True)
    return outputs, start, start_command


@app.cell
def __(os, sp, sys):
    def gridlabd_bin(*args,**kwargs):
        """Run gridlabd
        Arguments:
        - *args: command arguments
        - **kwargs: global definitions (placed before command arguments)
        """
        cmd = ["gridlabd.bin" if "GLD_BIN" in os.environ else "gridlabd"]
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

    gridlabd_version = gridlabd_bin("--version")
    gridlabd_copyright = gridlabd_bin("--copyright")
    gridlabd_license = gridlabd("--license")
    return (
        gridlabd,
        gridlabd_bin,
        gridlabd_copyright,
        gridlabd_license,
        gridlabd_version,
    )


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
