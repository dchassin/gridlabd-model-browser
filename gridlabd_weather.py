import marimo

__generated_with = "0.1.55"
app = marimo.App(width="full")


@app.cell
def __(gridlabd, mo):
    #
    # Gridlabd version
    #
    gridlabd_version = gridlabd("--version", binary=True, split=True)
    mo.vstack([mo.hstack([mo.md("# GridLAB-D NSRDB Weather"),mo.md(gridlabd_version[0])]),mo.md("---")])
    return gridlabd_version,


@app.cell
def __(get_apikey, get_whoami, gridlabd, json, os, set_apikey, set_whoami):
    #
    # NSRDB credentials
    #
    credentials = f"{os.environ['HOME']}/.nsrdb/credentials.json"
    def load_credentials():
        try:
            with open(credentials,"r") as fh:
                whoami,apikey = list(json.load(fh).items())[0]
                set_whoami(whoami)
                set_apikey(apikey)
        except:
            set_whoami(None)
            set_apikey(None)

    def send_registration(_):
        if get_whoami() is None:
            gridlabd("nsrdb_weather",f"--signup={get_whoami()}")

    def save_credentials(_):
        if get_whoami() and get_apikey():
            with open(credentials,"w") as fh:
                json.dump(fh,{get_whoami():get_apikey()})

    load_credentials()
    return (
        credentials,
        load_credentials,
        save_credentials,
        send_registration,
    )


@app.cell
def __(get_fields, mo, setting_graphxaxis, setting_graphyaxis):
    #
    # Plotting options
    #
    xaxis = mo.ui.dropdown(options=get_fields() if get_fields() else [],
                           label="X Axis:",
                           value=setting_graphxaxis.value if get_fields() else None)
    yaxis = mo.ui.multiselect(options=get_fields() if get_fields() else [],
                              label="Y Axis:",
                              value=[setting_graphyaxis.value] if get_fields() else None)
    grid = mo.ui.switch()
    marker = mo.ui.dropdown(label="Marker:",
                            options=["none",".","x","+","o","^","v"],
                            value="none")
    line = mo.ui.dropdown(label="Line:", 
                          options=["none","solid","dotted","dashed","dashdot"],
                          value="solid")
    return grid, line, marker, xaxis, yaxis


@app.cell
def __(geolocator, mo, set_city, set_latitude, set_longitude):
    #
    # City finder
    #
    def find_city(*args,**kwargs):
        set_city(location.value)
        loc = geolocator.geocode(location.value)
        set_latitude(f"{loc.latitude:.2f}")
        set_longitude(f"{loc.longitude:.2f}")
    location = mo.ui.text(label = "Search for location:")  
    return find_city, location


@app.cell
def __(download_csv, download_glm, find_city, location, mo):
    #
    # Location lookup
    #
    lookup = mo.ui.button(label = "Find",on_click=find_city)
    mo.hstack([mo.hstack([location,lookup],justify='start'),
               mo.hstack([download_csv,download_glm],justify='start'),
              ])
    return lookup,


@app.cell
def __(
    geolocator,
    get_latitude,
    get_longitude,
    interpolation,
    latitude,
    longitude,
    mo,
    preview,
    year,
):
    #
    # Weather location
    #
    try:
        _addr = geolocator.reverse(f"{get_latitude()},{get_longitude()}").raw["address"]
    except:
        _addr = None
    mo.vstack([
        mo.hstack([mo.md(f"{_addr.get('city','')}, {_addr.get('state','')} ({_addr.get('country','')})" if _addr else ""),
                   preview,
                  ],
                 justify='start',
                 ),
        mo.hstack([latitude,
                   longitude,
                   year,
                   interpolation],
                  justify='start',
                 ),
    ])

    return


@app.cell
def __(
    get_csv,
    get_df,
    get_glm,
    get_latitude,
    get_longitude,
    get_whoami,
    grid,
    gridlabd,
    io,
    line,
    marker,
    mo,
    pd,
    set_csv,
    set_df,
    set_fields,
    set_glm,
    setting_weathercsv,
    setting_weatherglm,
    setting_weatherobj,
    settings,
    xaxis,
    yaxis,
):
    #
    # Preview
    #
    def preview(_):
        data = io.StringIO(
            gridlabd("nsrdb_weather",
                     f"-y={year.value}",
                     f"-p={latitude.value},{longitude.value}",
                    )
        )
        df = pd.read_csv(data,parse_dates=True)
        set_df(df)
        set_csv(df.to_csv(index=False,header=False))
        set_fields(list(df.columns))
        gridlabd("nsrdb_weather",
                 f"--csv={setting_weathercsv.value}",
                 f"--glm={setting_weatherglm.value}",
                 f"--name={setting_weatherobj.value}",
                 f"--interpolate={interpolation.value}",
                 f"-y={year.value}",
                 f"-p={latitude.value},{longitude.value}",
                )
        with open("weather.glm","r") as glm:
            set_glm(glm.read())

    def get_table():
        if get_df() is None:
            return
        return mo.ui.table(get_df(), page_size=24)

    def get_graph():
        if get_df() is None:
            return
        return mo.vstack([
            mo.hstack([xaxis,yaxis,mo.md("Grid:"),grid,line,marker],justify='start'),
            get_df().plot(figsize = (15,10),
                     x = xaxis.value,
                     y = yaxis.value,
                     grid = grid.value,
                     marker = marker.value,
                     linestyle = line.value,
                    ) 
                if xaxis.value and yaxis.value else mo.md("Choose fields")
        ])

    def get_text():
        glm = get_glm()
        if glm is None:
            return
        return mo.ui.text_area(value = glm,
                               full_width = True,
                              )

    table = get_table()
    graph = get_graph()
    text = get_text()

    year = mo.ui.number(start=2000, stop=2020, label="Year:", value=2020)
    latitude = mo.ui.text(label="Latitude:", value=get_latitude())
    longitude = mo.ui.text(label="Longitude:", value=get_longitude())
    interpolation = mo.ui.dropdown(label="Interpolation (min):", options=["60","30","20","15","10","5","1"],value="60")
    preview = mo.ui.button(label="Preview", on_click=preview)
    download_glm = mo.download(label="GLM", 
                           data = get_glm(), 
                           filename = setting_weatherglm.value, 
                           disabled = (get_glm() == ""), 
                           mimetype = "text/plain")
    download_csv = mo.download(label="CSV", 
                           data = get_csv(), 
                           filename = setting_weathercsv.value, 
                           disabled = (get_csv() == ""), 
                           mimetype = "text/csv")
    nodata = mo.md(("No data" if get_whoami() else "You must register with NSRDB first (see Settings).") + "\n"*10)

    body = mo.vstack([
        mo.tabs({
            "Graph" : graph if graph else nodata,
            "Table" : table if table else nodata,
            "GLM" : text if text else nodata,
            "Settings" : settings,
            }),
    ])

    mo.vstack([
        body
    ])
    return (
        body,
        download_csv,
        download_glm,
        get_graph,
        get_table,
        get_text,
        graph,
        interpolation,
        latitude,
        longitude,
        nodata,
        preview,
        table,
        text,
        year,
    )


@app.cell
def __(mo, settings_credentials, settings_glmfile, settings_weatherdata):
    #
    # Settings
    #
    settings = mo.accordion({
        "NSRDB Credentials" : settings_credentials,
        "Weather Data" : settings_weatherdata,
        "GLM File" : settings_glmfile,
        })
    return settings,


@app.cell
def __(mo):
    #
    # GLM settings
    #
    setting_weatherobj = mo.ui.text(label = "Weather object name", value = "weather")
    setting_weathercsv = mo.ui.text(label = "Weather CSV name", value = "weather.csv")
    setting_weatherglm = mo.ui.text(label = "Weather GLM name", value = "weather.glm")
    settings_glmfile = mo.vstack([
        setting_weatherobj,
        setting_weathercsv,
        setting_weatherglm,
    ])
    return (
        setting_weathercsv,
        setting_weatherglm,
        setting_weatherobj,
        settings_glmfile,
    )


@app.cell
def __(get_apikey, get_whoami, mo):
    #
    # NSRDB credentials settings
    setting_email = mo.ui.text(label = "Registration email", 
                               kind = "email", 
                               placeholder = "user.name@company.org",
                               value = get_whoami() if get_whoami() else "")
    setting_apikey = mo.ui.text(label = "Registered API key", 
                                kind = "password", 
                                placeholder = "Paste API key here",
                                value = get_apikey() if get_apikey() else "")
    setting_register = mo.ui.button(label="Register")
    settings_credentials = mo.vstack([
        mo.hstack([setting_email,setting_register],justify='start'),
        setting_apikey,
    ])


    return (
        setting_apikey,
        setting_email,
        setting_register,
        settings_credentials,
    )


@app.cell
def __(mo):
    #
    # Weather graph settings
    #
    setting_graphxaxis = mo.ui.text(label = "Weather graph default x-axis", value = "datetime")
    setting_graphyaxis = mo.ui.text(label = "Weather graph default y-axis", value = "temperature[degF]")
    settings_weatherdata = mo.vstack([
        setting_graphxaxis,
        setting_graphyaxis,
    ])
    return setting_graphxaxis, setting_graphyaxis, settings_weatherdata


@app.cell
def __(mo):
    #
    # UI state variables
    #
    get_city, set_city = mo.state(None)
    get_location, set_location = mo.state("")
    get_latitude, set_latitude = mo.state("")
    get_longitude, set_longitude = mo.state("")
    get_df, set_df = mo.state(None)
    get_csv, set_csv = mo.state("")
    get_glm, set_glm = mo.state("")
    get_fields, set_fields = mo.state(None)
    get_whoami, set_whoami = mo.state(None)
    get_apikey, set_apikey = mo.state(None)
    return (
        get_apikey,
        get_city,
        get_csv,
        get_df,
        get_fields,
        get_glm,
        get_latitude,
        get_location,
        get_longitude,
        get_whoami,
        set_apikey,
        set_city,
        set_csv,
        set_df,
        set_fields,
        set_glm,
        set_latitude,
        set_location,
        set_longitude,
        set_whoami,
    )


@app.cell
def __():
    #
    # Initialization
    #
    import marimo as mo
    import os, sys, io, json
    import subprocess as sp
    import pandas as pd
    import geopy as gp
    from geopy.geocoders import Nominatim
    from gridlabd_runner import gridlabd

    geolocator = Nominatim(user_agent="marimo")
    return (
        Nominatim,
        geolocator,
        gp,
        gridlabd,
        io,
        json,
        mo,
        os,
        pd,
        sp,
        sys,
    )


@app.cell
def __(mo):
    mo.vstack([
        mo.md("---"),
        mo.md("*Copyright (C) 2023, Regents of the Leland Stanford Junior University*")
    ])
    return


if __name__ == "__main__":
    app.run()
