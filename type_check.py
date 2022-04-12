import inspect
from functools import wraps
from typing import Iterable, Union

NoneType = type(None)  # from types import NoneType (python 3.10 or later)

__author__ = "Lingxuan Ye"
__version__ = "2.4.3"
__all__ = ["type_check", "element_type_check", "debug"]


class Error(Exception):
    pass


class Warning(Exception):
    pass


def _literal(type_: type, with_quotes: bool = True):
    type_literal = str(type_).split("'")[1]
    if with_quotes:
        return "'" + type_literal + "'"
    else:
        return type_literal


def _deduplicate(list_: list):
    temp = list_.copy()
    list_.clear()
    for i in temp:
        if i not in list_:
            list_.append(i)


def _reform(errors: list):
    if len(errors) <= 1:
        return
    is_first_iteration = True
    type_literals = []
    for error in errors:
        if is_first_iteration:
            template = error.split("'")
            is_first_iteration = False
        type_literal = "'" + error.split("'")[3] + "'"
        type_literals.append(type_literal)
    type_info = ", ".join(type_literals[0:-1]) + f" or {type_literals[-1]}"
    template.pop(3)
    template.insert(3, type_info.strip("'"))
    errors.clear()
    errors.append("'".join(template))


def _type_check(argument,
                annotation,
                parameter_name: str,
                __in_recursion: bool = False) -> dict:
    result = {"error": [], "warning": []}
    if annotation is inspect._empty:
        return result
    if isinstance(annotation, (list, tuple, set)):
        warning = f"informal annotation for parameter '{parameter_name}', " \
                + "try to use 'typing.Union' instead of a collection of types"
        result["warning"].append(warning)
        for type_ in annotation:
            _result = _type_check(argument, type_, parameter_name, True)
            result["error"].extend(_result["error"])
            result["warning"].extend(_result["warning"])
            if not _result["error"]:  # len(_result["error"]) == 0
                result["error"].clear()
                break
        if not __in_recursion:
            _deduplicate(result["error"])
            _reform(result["error"])
            _deduplicate(result["warning"])
        return result
    if annotation is None:
        warning = "informal annotation for " \
                        + f"parameter '{parameter_name}', " \
                        + "try to use 'types.NoneType' " \
                        + "(python 3.10 or later) " \
                        + "or 'type(None)' instead of 'None'"
        result["warning"].append(warning)
        annotation = NoneType
    if not isinstance(argument, annotation):
        try:
            type_str = _literal(annotation)
        except IndexError:
            type_str = "'" + str(annotation) + "'"
        error = f"argument '{parameter_name}' must be " \
              + f"{type_str}, not {_literal(type(argument))}"
        result["error"].append(error)
    return result


def type_check(func, *, raise_error: bool = True, raise_warning: bool = False):
    """
    'raise_error' and 'raise_warning' are always set to default
    unless explicitly call this function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        errors = []
        warnings = []
        sig = inspect.signature(func)
        bound_arguments = sig.bind(*args, **kwargs)
        bound_arguments.apply_defaults()
        arguments = bound_arguments.arguments
        parameters = sig.parameters
        for parameter_name in parameters.keys():
            argument = arguments[parameter_name]
            annotation = parameters[parameter_name].annotation
            _result = _type_check(argument, annotation, parameter_name)
            errors.extend(_result["error"])
            warnings.extend(_result["warning"])
        if errors:  # len(error) != 0
            error_info = "\n".join((f"- {i}" for i in errors))
            if raise_error:
                raise Error("\n" + error_info)
            else:
                print(f"Error(s):\n{error_info}\n")
        if warnings:  # len(warning) != 0:
            warning_info = "\n".join((f"- {i}" for i in warnings))
            if raise_warning:
                raise Warning("\n" + warning_info)
            else:
                print(f"Warning(s):\n{warning_info}\n")
        return func(*args, **kwargs)

    return wrapper


@type_check
def element_type_check(iterable_: Iterable,
                       type_required,
                       iterable_name: str = "",
                       raise_error: bool = True):
    if not iterable_:  # len(iterable_) == 0
        error_info = "- argument 'iterable_' cannot be empty"
        if raise_error:
            raise Error("\n" + error_info)
        else:
            print(f"Error:\n{error_info}\n")
            return
    errors = []
    warnings = []
    if iterable_name == "":
        iterable_name = "_"
    for index, element in enumerate(iterable_):
        _result = _type_check(element, type_required,
                              f"{iterable_name}[{index}]")
        errors.extend(_result["error"])
        warnings.extend(_result["warning"])
    if errors:  # len(error) != 0
        error_info = "\n".join((f"- {i}" for i in errors))
        if raise_error:
            raise Error("\n" + error_info)
        else:
            print(f"Error(s):\n{error_info}\n")


@type_check
def debug(argument, type_required, parameter_name: str):
    _type_check(argument, type_required, parameter_name)
