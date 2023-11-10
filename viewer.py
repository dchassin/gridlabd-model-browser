import marimo

__generated_with = "0.1.47"
app = marimo.App(width="full")


@app.cell
def __(load_glm, mo, set_file):
    #
    # File upload
    #
    filename = mo.ui.file(
        filetypes=[".json"],
        kind="button",
        label="GridLAB-D model file (JSON)",
        on_change=lambda x: set_file(load_glm(x)),
    )
    filename
    return filename,


@app.cell
def __(filename, mo):
    #
    # Filename witness
    #
    mo.md(f"**Current file**: `{filename.name(0)}`")
    return


@app.cell
def __(err, json, mo, pd, set_status):
    #
    # Model data load
    #
    def load_glm(upload):
        if upload is None:
            set_status("Select a file to view")
            return pd.DataFrame({})
        try:
            glm = json.loads(upload[0].contents.decode())
            assert glm["application"] == "gridlabd"
            assert glm["version"] >= "4.3.3"
            data = pd.DataFrame(glm["objects"]).transpose()
            data.index.name = "name"
            data.reset_index(inplace=True)
            if "latitude" in data and "longitude" in data:
                data['latitude'] = [float(x) for x in data['latitude']]
                data['longitude'] = [float(x) for x in data['longitude']]
                nodes = data.loc[~data["latitude"].isnull()&~data["longitude"].isnull()]
                lines = data.loc[~data["from"].isnull()&~data["to"].isnull()]
            else:
                nodes = None
                lines = None
            data.set_index(["class","name"],inplace=True)
            classes = {}
            for oclass in data.index.get_level_values(0).unique():
                classes[oclass] = data.loc[oclass].dropna(axis=1,how='all')
            set_status(f"File '{upload[0].name}' contains {len(data)} objects.")
            return dict(
                data = data,
                classes = classes,
                nodes = nodes,
                lines = lines)
        except Exception as err:
            set_status(f"Exception: {err}!")

    get_file, set_file = mo.state(load_glm(None))

    return get_file, load_glm, set_file


@app.cell
def __(mo):
    #
    # State variables
    #
    get_status, set_status = mo.state("")
    return get_status, set_status


@app.cell
def __(get_file, get_view, mo, set_map):
    #
    # Model data display
    #
    _data = get_file()
    if _data is None:
        selector = mo.md("Invalid model")
    elif len(_data) == 0:
        selector = mo.md("No GridLAB-D objects to view")
    else:
        keys = list(_data["classes"])
        class_select = mo.ui.dropdown(options = keys,
                                      allow_select_none = False,
                                      value = keys[0],
                                      )
        with_header = mo.ui.switch(value=False)
        map_type = mo.ui.switch(value=False,on_change=set_map)
        selector = mo.hstack([mo.md("Select object class to display: "),
                   class_select,
                   mo.md("Show header data"),
                   with_header,
                   mo.md("Satellite view:") if get_view() else "",
                   map_type if get_view() else "",
                  ],justify='start')
    selector
    return class_select, keys, map_type, selector, with_header


@app.cell
def __(get_file, mo, px):
    #
    # Map data
    #
    def get_map(satellite):
        if get_file() is None or "data" not in get_file() or len(get_file()["data"]) == 0:
            return None
        data = get_file()["data"]
        nodes = get_file()["nodes"]
        lines = get_file()["lines"]
        if nodes is None or len(nodes) == 0:
            return None

        # nodes
        map = px.scatter_mapbox(
            # hover_data = nodes.index,
            lat = nodes['latitude'],
            lon = nodes['longitude'],
            hover_name = nodes['name'],
            zoom = 15,
            # TODO: add hover_data flags, e.g., dict(field:bool,...)
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
        map.add_trace(dict(hovertemplate = names,
                           lat = lats,
                           lon = lons,
                           line = dict(color='#636efa'),
                           mode = 'lines',
                           subplot = 'mapbox',
                           type = 'scattermapbox',
                           showlegend = False))
        
        if satellite:
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
        return map

    def set_map(satellite):
        set_view(get_map(satellite))

    get_view, set_view = mo.state(get_map(False))

    return get_map, get_view, set_map, set_view


@app.cell
def __(class_select, get_file, mo, set_status, with_header):
    #
    # Table data display
    #
    def select_item(x):
        return

    _data = get_file()
    if not _data is None and "classes" in _data and len(_data["classes"]) > 0 and class_select.selected_key:
        _classes = _data["classes"]
        values = _classes[class_select.value].copy()
        if with_header.value == False:
            values.drop(["id","rank","clock","rng_state","guid","flags","parent"],inplace=True,axis=1,errors='ignore')
        table_view = mo.ui.table(values,pagination=True,selection='single',on_change=select_item)
        set_status(f"Class '{class_select.value}' has {len(values)} objects.")
    else:
        table_view = None

    return select_item, table_view, values


@app.cell
def __(get_view, mo, table_view):
    #
    # Show the chosen view
    #
    if get_view():
        result = mo.tabs({
            "Table" : table_view,
            "Map" : get_view(),
        })
    else:
        result = table_view
    result
    return result,


@app.cell
def __(get_status, mo):
    #
    # Status information
    #
    mo.md(f"""
    ---

    {get_status()}
    """)
    return


@app.cell
def __():
    #
    # Requirements
    #
    import os, sys, json
    import subprocess
    import marimo as mo
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    return go, json, mo, np, os, pd, px, subprocess, sys


if __name__ == "__main__":
    app.run()
