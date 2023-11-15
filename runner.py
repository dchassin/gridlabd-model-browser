import marimo

__generated_with = "0.1.39"
app = marimo.App(width="full")


@app.cell
def __():
    import marimo as mo
    mo.md(f"""<iframe height="800px" width="100%" src="http://localhost:2718" title="Test"></iframe>""")
    return mo,


@app.cell
def __(mo):
    mo.__app__
    return


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
