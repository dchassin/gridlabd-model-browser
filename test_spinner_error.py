import marimo

__generated_with = "0.1.39"
app = marimo.App()


@app.cell
def __(err):
    import marimo as mo
    def hit(x):
        try:
            with mo.status.spinner("Testing"):
                raise Exception("error")
        except Exception as err:
            print(err)

    button = mo.ui.button(label="Hit me!",on_click=hit)
    button
    return button, hit, mo


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
