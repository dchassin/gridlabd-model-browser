import marimo

__generated_with = "0.1.43"
app = marimo.App(width="full")


@app.cell
def __(load_glm, mo, set_file):
    #
    # File upload
    #
    filename = mo.ui.file(
        filetypes = [".glm",".json"],
        kind = "button",
        multiple = True,
        label = "GridLAB-D model file",
        on_change = lambda x:set_file(load_glm(x[0].name)))
    filename
    return filename,


@app.cell
def __(err, json, mo, pd, set_status, subprocess):
    #
    # Model data load
    #
    def load_glm(filename):
        if not filename:
            set_status("Select a file to view")
            return pd.DataFrame({})
        set_status(f"Loading {filename}...")
        if filename.endswith(".json"):
            jsonfile = filename
        else:
            jsonfile = filename.replace(".glm",".json")
            result = subprocess.run(["gridlabd", "-I", filename, "-o", jsonfile],
                                    text = True,
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.STDOUT,
                                   )
            if result.returncode != 0:
                set_status(f"""GridLAB-D errors detected:
    ~~~
    {result.stdout}
    ~~~""")
                return None
        with open(jsonfile, "r") as fh:
            try:
                glm = json.load(fh)
                assert glm["application"] == "gridlabd"
                assert glm["version"] >= "4.3.3"
                data = pd.DataFrame(glm["objects"]).transpose()
                data.index.name = "name"
                # return data
                data.reset_index(inplace=True)
                data.set_index(["class","name"],inplace=True)
                result = {}
                for oclass in data.index.get_level_values(0).unique():
                    result[oclass] = data.loc[oclass].dropna(axis=1,how='all')
                set_status(f"File '{filename}' contains {len(data)} objects.")
                return result
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
def __(get_file, mo):
    #
    # Model data display
    #
    data = get_file()
    if data is None:
        selector = mo.md("Invalid model")
    elif len(data) == 0:
        selector = mo.md("No GridLAB-D objects to view")
    else:
        keys = list(data)
        class_select = mo.ui.dropdown(options = keys,
                                      allow_select_none = False,
                                      value = keys[0],
                                      )
        with_header = mo.ui.switch(value=False)
        selector = mo.hstack([mo.md("Select object class to display: "),
                   class_select,
                   mo.md("Show header data"),
                   with_header,
                  ],justify='start')
    selector
    return class_select, data, keys, selector, with_header


@app.cell
def __(class_select, data, mo, set_status, with_header):
    #
    # Class data display
    #
    def select_item(x):
        return

    if not data is None and len(data) > 0 and class_select.selected_key:
        values = data[class_select.value].copy()
        if with_header.value == False:
            values.drop(["id","rank","clock","rng_state","guid","flags","parent"],inplace=True,axis=1,errors='ignore')
        table_view = mo.ui.table(values,pagination=True,selection='single',on_change=select_item)
        set_status(f"Class '{class_select.value}' has {len(values)} objects.")
    else:
        table_view = None
    table_view
    return select_item, table_view, values


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
    import marimo as mo
    import pandas as pd
    import subprocess
    return json, mo, os, pd, subprocess, sys


if __name__ == "__main__":
    app.run()
