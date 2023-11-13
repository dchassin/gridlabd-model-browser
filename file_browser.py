import marimo

__generated_with = "0.1.39"
app = marimo.App(width="full")


@app.cell
def __(change_tabs, file_browser):
    from browser import *
    change_tabs("model.json",True)
    file_browser(download=True,size=True,preview=True,heading=True)
    return *,


if __name__ == "__main__":
    app.run()
