import inspect
from functools import wraps
from typing import Iterable

NoneType = type(None)  # from types import NoneType (python 3.10 or later)

__author__ = "Lingxuan Ye"
__version__ = "2.2.0"
__all__ = ["type_check", "element_type_check"]


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


def _reform(errors: list):
    type_literals = []
    flag = True
    for index, error in enumerate(errors.copy()):
        if error.startswith("argument"):
            if flag:
                arg_error_index = index
                template = error.split("'")
                flag = False
            type_literal = error.split("'")[3]
            type_literals.append(type_literal)
            errors.remove(error)
    if len(type_literals) <= 1:
        return
    type_info = ", ".join(type_literals[0:-1]) + f" or {type_literals[-1]}"
    template.pop(3)
    template.insert(3, type_info)
    arg_error = "'".join(template)
    errors.insert(arg_error_index, arg_error)


def _type_check(argument,
                type_required: type,
                parameter_name: str,
                __in_recursion: bool = False) -> dict:
    result = {"error": [], "warning": []}
    if type_required is inspect._empty:
        return result
    if isinstance(type_required, (list, tuple, set)):
        warning = f"informal annotation for parameter '{parameter_name}', " \
                + "try to use 'typing.Union' instead"
        result["warning"].append(warning)
        for type_ in type_required:
            _result = _type_check(argument, type_, parameter_name, True)
            if not _result["error"] and not _result["warning"]:
                # _result == result = {"error": [], "warning": []}
                result["error"].clear()
                del result["warning"][-1:0:-1]
                break
            result["error"].extend(_result["error"])
            result["warning"].extend(_result["warning"])
            if not __in_recursion:
                _reform(result["error"])
        return result
    if not isinstance(type_required, type):
        if type_required is not None:
            error = f"annotation for parameter '{parameter_name}' " \
                  + "must be a type"
            result["error"].append(error)
            return result
        else:
            warning = "informal annotation for " \
                    + f"parameter '{parameter_name}', " \
                    + "try to use 'types.NoneType' (python 3.10 or later) " \
                    + "or 'type(None)' instead"
            result["warning"].append(warning)
            type_required = NoneType
    if isinstance(argument, type_required):
        return result
    else:
        error = f"argument '{parameter_name}' must be " \
              + f"{_literal(type_required)}, not {_literal(type(argument))}"
        result["error"].append(error)
        return result


def type_check(func, *, raise_error: bool = True, raise_warning: bool = False):
    """
    This is a decorator.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        bound_arguments = sig.bind(*args, **kwargs)
        bound_arguments.apply_defaults()
        arguments = bound_arguments.arguments
        parameters = sig.parameters
        error = []
        warning = []
        for parameter_name in parameters.keys():
            argument = arguments[parameter_name]
            annotation = parameters[parameter_name].annotation
            _result = _type_check(argument, annotation, parameter_name)
            error.extend(_result["error"])
            warning.extend(_result["warning"])
        if raise_error and error:  # len(error) != 0
            error_info = "\n" + "\n".join(error)
            raise Error(error_info)
        if raise_warning and warning:  # len(warning) != 0:
            warning_info = "\n" + "\n".join(warning)
            raise Warning(warning_info)
        return func(*args, **kwargs)

    return wrapper


@type_check
def element_type_check(iterable_: Iterable,
                       type_required: type,
                       iterable_name: str,
                       with_supplement: bool = False,
                       raise_exception: bool = True):
    """
    If the argument 'raise_exception' is set to False,
    function 'element_type_check' will return error info if type check fails.

    If the argument 'raise_exception' is set to True,
    function 'element_type_check' will raise exception if type check fails.
    """

    if not iterable_:  # len(iterable_) == 0
        error_info = "argument 'iterable_' cannot be empty"
        if raise_exception:
            raise Error("\n" + error_info)
        else:
            return error_info
    if iterable_name == "":
        iterable_name = "_"
    for index, element in enumerate(iterable_):
        error_info = _type_check(element, type_required,
                                 f"{iterable_name}[{index}]")
        if error_info is not None:
            if with_supplement:
                error_info += f", if a(n) {_literal(type(iterable_))} is given"
            break
    if raise_exception:
        raise Error("\n" + error_info)
    else:
        return error_info
