__all__ = ["handcalc"]

from typing import Optional
from functools import wraps
import inspect
import innerscope
from .handcalcs import LatexRenderer


def handcalc(
    override: str = "",
    precision: int = 3,
    left: str = "",
    right: str = "",
    scientific_notation: Optional[bool] = True,
    decimal_separator: str = ".",
    jupyter_display: bool = True,
):
    def handcalc_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            line_args = {
                "override": override,
                "precision": precision,
                "sci_not": scientific_notation,
            }
            func_source = inspect.getsource(func)
            cell_source = _func_source_to_cell(func_source)
            # use innerscope to get the values of locals, closures, and globals when calling func
            scope = innerscope.call(func, *args, **kwargs)
            LatexRenderer.dec_sep = decimal_separator
            renderer = LatexRenderer(cell_source, scope, line_args)
            latex_code = renderer.render()
            if jupyter_display:
                try:
                    from IPython.display import Latex, display
                except ModuleNotFoundError:
                    ModuleNotFoundError(
                        "jupyter_display option requires IPython.display to be installed."
                    )
                if not "& \\textrm{" in latex_code:
                    display(Latex(latex_code))
                else:
                    display_latex_and_markdown(latex_code)
                return scope.return_value

            # https://stackoverflow.com/questions/9943504/right-to-left-string-replace-in-python
            latex_code = "".join(latex_code.replace("\\[", "", 1).rsplit("\\]", 1))
            return (left + latex_code + right, scope.return_value)

        return wrapper

    return handcalc_decorator


def _func_source_to_cell(source: str):
    """
    Returns a string that represents `source` but with no signature, doc string,
    or return statement.

    `source` is a string representing a function's complete source code.
    """
    source_lines = source.split("\n")
    acc = []
    doc_string = False
    for line in source_lines:
        if (
            not doc_string
            and line.lstrip(" \t").startswith('"""')
            and line.lstrip(" \t").rstrip().endswith('"""', 3)
        ):
            doc_string = False
            continue
        elif (
            not doc_string
            and line.lstrip(" \t").startswith('"""')
            and not line.lstrip(" \t").rstrip().endswith('"""', 3)
        ):
            doc_string = True
            continue
        elif doc_string and '"""' in line:
            doc_string = False
            continue
        if (
            "def" not in line
            and not doc_string
            and "return" not in line
            and "@" not in line
        ):
            acc.append(line)
    return "\n".join(acc)


def display_latex_and_markdown(latex_code: str):
    try:
        from IPython.display import Latex, Markdown, display
    except ModuleNotFoundError:
        ModuleNotFoundError(
            "jupyter_display option requires IPython.display to be installed."
        )
    latex_code = latex_code.split("\n")
    latex_start = "\n".join(latex_code[:2])
    latex_end = "\n".join(latex_code[-2:])

    latex = latex_start
    for line in latex_code[2:-2]:
        if not line.startswith("& \\textrm{"):
            latex = "\n".join([latex, line])
            continue

        if latex != latex_start:
            latex = "\n".join([latex, latex_end])
            display(Latex(latex))
            latex = latex_start

        line = line[line.find("{") + 1 : line.find("}")].strip()
        display(Markdown(line))

    if latex != latex_start:
        latex = "\n".join([latex, latex_end])
        display(Latex(latex))
