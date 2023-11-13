import marimo

__generated_with = "0.1.48"
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
    last_stderr,
    loads,
    mo,
    model_stats,
    network,
    recorders,
    reference_model,
    results,
    results_preview,
    settings,
    start_preview,
    starttime,
    state,
    stoptime,
    timezone,
    weather_stats,
):
    project_name = mo.ui.text(label="Project name",value="untitled-0",disabled=True)
    save = mo.ui.button(label="Save",disabled=True)
    load = mo.ui.button(label="Load",disabled=True)
    mo.vstack([
        mo.hstack([
            mo.md("""# <a href="https://www.arras.energy/" target="_blank">Arras Energy</a>"""),
            mo.md(f"""<br/><a href="http://source.gridlabd.us/" target="_blank">{gridlabd_version[0]}</a>""")    
        ]),
        mo.hstack([
            project_name,
            load,
            save
        ],justify='start'),
        mo.md("---"),
        mo.tabs({
            "Network" : mo.vstack([
                mo.hstack([network,reference_model]),
                mo.ui.table(model_stats,selection=None) if not model_stats is None else mo.md("No model info"),
                mo.md(f"Error output:<font color=red>\n```\n{last_stderr}\n```\n</font>" if last_stderr else ''),
                ]),
            "Weather" : mo.vstack([
                mo.hstack([state,city],justify="start"),
                mo.ui.table(weather_stats,selection=None) if not weather_stats is None else mo.md("No weather info"),
                ]),
            "Clock" : mo.vstack([
                mo.hstack([starttime,stoptime,timezone],justify="start"),
                clock,
                ]),
            "Loads" : mo.md("No load models available"),
            "Meters" : mo.md("No meter data available"),
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
            "Settings" : settings,
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
    return load, project_name, save


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
    # Reference models
    #
    _models = gridlabd("model","index")
    reference_model = mo.ui.dropdown(options=_models,label="Reference model")
    return reference_model,


@app.cell
def __(glob, mo, os, reference_model):
    #
    # Model file
    #
    if reference_model.value:
        _glm = f"{os.path.basename(reference_model.value)}.glm"
    else:
        _glm = None
    _files = [x for x in glob.glob("*.glm") if not x.startswith("_")]
    network = mo.ui.dropdown(label="Network model",options=_files,value=_glm)
    return network,


@app.cell
def __(gridlabd, reference_model):
    #
    # Download model
    #
    if reference_model.value:
        gridlabd("model","get",reference_model.value)
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
def __(
    gridlabd,
    json,
    network,
    pd,
    re,
    setting_repeatmsgs,
    setting_usemodules,
    sys,
):
    network.value#
    # Compile the model
    #
    active_modules = ""
    if setting_usemodules:
        active_modules = " ".join([f"-M {x}" for x in setting_usemodules.value])
    model = {}
    model_stats = None
    if network.value: # and state.value and city.value and timezone.value:
        jsonfile = network.value.replace(".glm",".json")
        try:
            _modules = active_modules.strip().split()
            gridlabd(*_modules,"-C",network.value,"-o",jsonfile,binary=True,
                     suppress_repeat_messages=str(setting_repeatmsgs.value).upper(),
                    )
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
        except:
            e_type, e_value, _ = sys.exc_info()
            model_stats = pd.DataFrame({"error":[f"{e_value} ({e_type.__name__})"]})

    return (
        active_modules,
        data,
        e_type,
        e_value,
        fh,
        jsonfile,
        model,
        model_stats,
        obj,
    )


@app.cell
def __(classes, mo, model, pd, setting_showheaders):
    #
    # Identify available objects and fields to records
    #
    if "objects" in model and "header" in model:
        _loads = pd.DataFrame(dict([(obj,data) for obj,data in model["objects"].items() if data["class"] in classes.value])).transpose().sort_index()
        if not setting_showheaders:
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
    _classes = sorted(model["classes"]) if "classes" in model else []
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
def __(
    active_modules,
    city,
    clock,
    loads,
    mo,
    model,
    network,
    os,
    recorders,
    setting_repeatmsgs,
    state,
):
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


    if "objects" in model: # and clock.value and recorders.value:
        start_command = f"gridlabd {active_modules} {network.value} _weather.glm _clock.glm _recorders.glm -D keep_progress=TRUE -D suppress_repeat_messages={str(setting_repeatmsgs.value).upper()}"
        outputs = [f"{x}.csv" for x in loads.value.index]
    else:
        start_command = ""
        outputs = []

    start = mo.ui.button(label="Start",on_click=_start,disabled=False if start_command else True)
    return outputs, start, start_command


@app.cell(disabled=True)
def __(get_file, mo, px):
    #
    # Map view
    #
    def load_map():
        if get_file() is None or "data" not in get_file() or len(get_file()["data"]) == 0:
            return None
        nodes = get_file()["nodes"]
        if nodes is None or len(nodes) == 0:
            return None
        lines = get_file()["lines"]
        data = get_file()["data"]

        # nodes
        # map = px.scatter_mapbox(
        #     lat = nodes['latitude'],
        #     lon = nodes['longitude'],
        #     hover_name = nodes['name'],
        #     text = nodes['name'] if get_labels() else None,
        #     zoom = 15,
        #     # TODO: add hover_data flags, e.g., dict(field:bool,...)
        # )
        map = px.scatter_mapbox(nodes,
                                lat = 'latitude',
                                lon = 'longitude',
                                hover_name = 'name',
                                text = 'name' if get_labels() else None,
                                zoom = 15,
                                hover_data = dict(
                                    latitude=False,
                                    longitude=False,
                                    nominal_voltage=True,
                                    phases=True,
                                ),
                               )

        # lines
        latlon = nodes.reset_index()[['name','latitude','longitude']].set_index('name')
        latlon = dict([(n,(xy['latitude'],xy['longitude'])) for n,xy in latlon.iterrows()])
        valid = [(n,x,y) for n,x,y in zip(lines['name'],lines['from'],lines['to']) if x in latlon and y in latlon]
        names = [None] * 3 * len(valid)
        names[0::3] = [x[0] for x in valid]
        names[1::3] = [x[0] for x in valid]
        lats = [None] * 3 * len(valid)
        lats[0::3] = [latlon[x[1]][0] for x in valid]
        lats[1::3] = [latlon[x[2]][0] for x in valid]
        lons = [None] * 3 * len(valid)
        lons[0::3] = [latlon[x[1]][1] for x in valid]
        lons[1::3] = [latlon[x[2]][1] for x in valid]
        map.add_trace(dict(hoverinfo = 'skip',
                           lat = lats,
                           lon = lons,
                           line = dict(color='#636efa'),
                           mode = 'lines',
                           subplot = 'mapbox',
                           type = 'scattermapbox',
                           showlegend = False))

        if get_satellite():
            map.update_layout(
                mapbox_style="white-bg",
                mapbox_layers=[
                    {
                        "below": 'traces',
                        "sourcetype": "raster",
                        "sourceattribution": "United States Geological Survey",
                        "source": [                 "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                        ],
                    },
                  ])
        else:    
            map.update_layout(mapbox_style="open-street-map")
        map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        set_mapview(map)

    get_labels, set_labels = mo.state(False)
    get_satellite, set_satellite = mo.state(False)
    get_mapview, set_mapview = mo.state(None)

    def change_labels(x):
        set_labels(x)
        load_map()

    def change_satellite(x):
        set_satellite(x)
        load_map()

    load_map()
    return (
        change_labels,
        change_satellite,
        get_labels,
        get_mapview,
        get_satellite,
        load_map,
        set_labels,
        set_mapview,
        set_satellite,
    )


@app.cell
def __(gridlabd_modules, mo):
    setting_graphtype = mo.ui.dropdown(["Altair","Plotly","Matplotlib"],"Altair")
    setting_showheaders = mo.ui.checkbox(False)
    setting_usemodules = mo.ui.multiselect(options=gridlabd_modules)
    setting_repeatmsgs = mo.ui.checkbox(True)
    _settings = {
        "Graph Type" : setting_graphtype,
        "Include Modules" : setting_usemodules,
        "Show Header Data" : setting_showheaders,
        "Suppress Repeat Messages" : setting_repeatmsgs,
    }
    settings = "<table>"
    for label,element in _settings.items():
        settings += f"<tr><td><b>{label}</b></td><td>{element}</td></tr>"
    settings += "</table>"

    return (
        element,
        label,
        setting_graphtype,
        setting_repeatmsgs,
        setting_showheaders,
        setting_usemodules,
        settings,
    )


@app.cell
def __(os, sp):
    last_stderr = None

    def gridlabd(*args,binary=False,**kwargs):
        """Run gridlabd
        Arguments:
        - *args: command arguments
        - **kwargs: global definitions (placed before command arguments)
        """
        cmd = ["gridlabd.bin" if binary and "GLD_BIN" in os.environ else "gridlabd"]
        for name,value in kwargs.items():
            cmd.extend(["-D", f"{name}={value}"])
        # cmd.extend(["-D",f"suppress_repeat_messages={str(setting_repeatmsgs.value).upper()}"])
        cmd.extend(args)
        # print(f"[Running '{' '.join(cmd)}']",file=sys.stdout)
        # with mo.status.spinner(f"Running command '{cmd}'"):
        global last_stderr
        last_stderr = None
        r = sp.run(cmd,capture_output=True,text=True)
        last_stderr = r.stderr
        if r.returncode != 0:
            raise Exception(f"gridlabd error code {r.returncode}")
        return r.stdout.strip().split("\n")

    gridlabd_version = gridlabd("--version=all",binary=True)
    gridlabd_copyright = gridlabd("--copyright",binary=True)
    gridlabd_license = gridlabd("--license")
    gridlabd_modules = [x.split()[0] for x in gridlabd("--modlist",binary=True)[2:]]
    return (
        gridlabd,
        gridlabd_copyright,
        gridlabd_license,
        gridlabd_modules,
        gridlabd_version,
        last_stderr,
    )


@app.cell
def __():
    import os, sys, re, io, json, glob
    import datetime as dt
    import marimo as mo
    import subprocess as sp
    import pandas as pd
    import altair as alt
    return alt, dt, glob, io, json, mo, os, pd, re, sp, sys


if __name__ == "__main__":
    app.run()
