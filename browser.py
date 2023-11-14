import os,glob,json,pandas as pd, marimo as mo

tabs = {}
def change_tabs(file,state):
    """Change tab state
    Arguments:
    - file (str): name of the file
    - state (bool): enables the tab
    """
    global tabs
    if state:
        ext = os.path.splitext(file)[1]
        if ext == ".csv":
            tabs[file] = mo.ui.table(data = pd.read_csv(file),pagination=True,selection=None)
        else:
            try:
                with open(file,"r") as fh:
                    data = fh.read()
            except FileNotFoundError:
                data = ""
            except Exception as err:
                e_type, e_value, _ = sys.exc_info()
                data = f"EXCEPTION [{e_type.__name__}]: {e_value}"
            tabs[file] = mo.ui.text_area(full_width = True,
                                         value = data,
                                         placeholder = "New file",
                                         disabled = not os.access(file,os.W_OK),
                                        )
    else:
        del tabs[file]
    return tabs

def file_browser(pattern = "*",
                 sort = False,
                 folders = False,
                 download = False,
                 preview = None,
                 size = None,
                 delete = False,
                 heading = "",
                 # page = [0,-1],
                ):
    """Build a marimo file browser
    Arguments:
    - pattern (str): pattern to use for filtering files
    - sort (bool|str|None): control sorting method
    - folders (bool): enable display of folders
    - download (bool) enable download button
    - preview (bool or None): enable preview
    - size (bool|str|None): enable/format file size display
    - delete (bool): enable file delete button
    - heading (bool|str): enable/format header
    """
    def fsize(file,format=False):
        size = os.stat(file).st_size
        if not format:
            return size
        elif format == True:
            format = "*{size:.1f}&nbsp;{unit}*"
        elif not type(format) is str:
            raise ValueError("format is invalid")
        if "unit" in format:
            unit = "B"
            for scale in ["kB","MB","GB","TB","PB","EB"]:
                if size < 1000:
                    break
                size /= 1000
                unit = scale
        else:
            unit = None
        return format.format(size=size,unit=unit)
    if heading == True:
        heading = f"# Listing of {pattern}"
    folders = {}
    listing = []
    checkbox = {}
    files = glob.glob(pattern)
    if sort:
        if not sort in ["desc","asc",True]:
            raise ValueError("sort is invalid")
        files = sorted(files,
                       reverse = True 
                           if sort == 'desc' 
                           else False)
    for id,file in enumerate(files):
        if os.path.isfile(file):
            if preview != None:
                checkbox[file] = mo.state(mo.ui.checkbox(on_change = lambda x:change_tabs(file,x),
                                                         value = (file in tabs)))
            listing.append(mo.hstack([
                mo.hstack([
                    checkbox[file][0]() if file in checkbox else mo.md(""),
                    mo.md(f"""**{file}** {fsize(file,size) 
                        if not size is None 
                        else ''}"""),
                ],justify='start'),
                mo.hstack([
                    mo.download(data = open(file,"rb"),
                                filename = file,
                                label = download 
                                    if type(download) is str 
                                    else "")
                        if download else mo.md(""),
                    mo.ui.button(label = delete 
                                     if type(delete) is str 
                                     else "X",
                                on_click = lambda x:os.remove(x),
                                ) 
                        if delete else mo.md(""),
                    ],justify='end')
            ],justify='space-between'))
        elif os.path.isdir(file):
            folders[f"`{file}`"] = file_browser(pattern = os.path.join(file,pattern),
                                                sort = sort,
                                                folders = folders,
                                                preview = False if type(preview) is bool else None,
                                                heading = None,
                                                download = download,
                                                size = size,
                                                delete = delete)
    return mo.vstack([
        mo.hstack([
            mo.md(heading if type(heading) is str else ""),
        ],justify='space-between'),
        mo.md("---"),
        mo.hstack([
            mo.vstack([
                mo.accordion(folders),
                mo.vstack(listing),
            ]),
            mo.tabs(tabs) if tabs and preview == True else mo.md("")
        ],justify="start",widths=[1,4]),
        mo.md("---"),
    ])
