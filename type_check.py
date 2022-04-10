import inspect
from functools import wraps
from typing import Iterable, Union

NoneType = type(None)  # from types import NoneType (python 3.10 or later)

__author__ = "Lingxuan Ye"
__version__ = "2.1.0"
__all__ = ["argument_check", "type_check", "element_type_check"]


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
    types = []
    flag = True
    for index, error in enumerate(errors.copy()):
        if error.startswith("argument"):
            if flag:
                arg_error_index = index
                template = error.split("'")
                flag = False
            type_ = error.split("'")[3]
            types.append(type_)
            errors.remove(error)
    if len(types) <= 1:
        return
    type_info = ", ".join(types[0:-1]) + f" or {types[-1]}"
    template.pop(3)
    template.insert(3, type_info)
    arg_error = "'".join(template)
    errors.insert(arg_error_index, arg_error)


def _argument_check(argument,
                    type_required: type,
                    parameter_name: str,
                    __in_recursion: bool = False) -> dict:
    result = {"warning": [], "error": []}
    if type_required is inspect._empty:
        return result
    if isinstance(type_required, (list, tuple, set)):
        warning = f"informal annotation for parameter '{parameter_name}', " \
                + "try to use 'typing.Union' instead"
        result["warning"].append(warning)
        for type_ in type_required:
            _result = _argument_check(argument, type_, parameter_name, True)
            if _result["is_valid"]:
                del result["warning"][-1:0:-1]
                result["error"].clear()
                break
            result["warning"].extend(_result["warning"])
            result["error"].extend(_result["error"])
            if not __in_recursion:
                _reform(result["error"])
        return result
    if type_required is None:
        warning = f"informal annotation for parameter '{parameter_name}', " \
                + "try to use 'types.NoneType' (python 3.10 or later) or " \
                + "'type(None)' instead"
        result["warning"].append(warning)
        type_required = NoneType
        if not isinstance(argument, NoneType):
            error = f"argument '{parameter_name}' must be 'NoneType', " \
                  + f"not {_literal(type(argument))}"
            result["error"].append(error)
        return result
    if not isinstance(type_required, type):
        error = f"annotation for parameter '{parameter_name}' must be a type"
        result["error"].append(error)
        return result
    if isinstance(argument, type_required):
        return result
    else:
        error = f"argument '{parameter_name}' must be " \
              + f"{_literal(type_required)}, not {_literal(type(argument))}"
        result["error"].append(error)
        return result


def argument_check(func,
                   *,
                   raise_error: bool = True,
                   raise_warning: bool = False):

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
            _result = _argument_check(argument, annotation, parameter_name)
            error.extend(_result["error"])
            warning.extend(_result["warning"])
        if raise_error and len(error) != 0:
            error_info = "\n" + "\n".join(error)
            raise Error(error_info)
        if raise_warning and len(warning) != 0:
            warning_info = "\n" + "\n".join(warning)
            raise Warning(warning_info)
        return func(*args, **kwargs)

    return wrapper


def type_check(argument,
               type_required: Union[type, tuple],
               parameter_name: str,
               check_input: bool = True,
               raise_exception: bool = True):
    """
    Deprecated.

    If the argument 'check_input' is set to True,
    function 'type_check' will check whether its arguments
    are valid.

    If the argument 'raise_exception' is set to False,
    function 'type_check' will return error info if type check fails.

    If the argument 'raise_exception' is set to True,
    function 'type_check' will raise exception if type check fails.
    """
    if not isinstance(check_input, bool):
        error_info = "argument 'check_input' must be 'bool', " \
                   + f"not {_literal(type(check_input))}"
        if raise_exception:
            raise Error("\n" + error_info)
        else:
            return error_info
    if check_input:
        type_check(type_required, (type, tuple), "type_required", False)
        if isinstance(type_required, tuple):
            for index, element in enumerate(type_required):
                type_check(element, type, f"type_required[{index}]", False)
        type_check(parameter_name, str, "arg_name", False)
        type_check(raise_exception, bool, "raise_exception", False)

    if isinstance(argument, type_required):
        return
    if isinstance(type_required, tuple):
        if len(type_required) == 0:
            error_info = "argument 'type_required' cannot be empty, " \
                       + "if a 'tuple' is given"
            if raise_exception:
                raise Error("\n" + error_info)
            else:
                return error_info
        type_list = []
        for type_ in type_required:
            type_list.append(_literal(type_))
        type_info = ", ".join(type_list[0:-1]) + f" or {type_list[-1]}"
    else:  # isinstance(type_required, type) == True
        type_info = _literal(type_required)
    error_info = f"argument '{parameter_name}' must be {type_info}, " \
               + f"not {_literal(type(argument))}"
    if raise_exception:
        raise Error("\n" + error_info)
    else:
        return error_info


def element_type_check(iterable_: Iterable,
                       type_required: Union[type, tuple],
                       iterable_name: str,
                       check_input: bool = True,
                       with_supplement: bool = False,
                       raise_exception: bool = True):
    """
    If the argument 'check_input' is set to True,
    function 'element_type_check' will check whether its arguments
    are valid.

    If the argument 'raise_exception' is set to False,
    function 'element_type_check' will return error info if type check fails.

    If the argument 'raise_exception' is set to True,
    function 'element_type_check' will raise exception if type check fails.
    """
    if not isinstance(check_input, bool):
        error_info = "argument 'check_input' must be 'bool', " \
                   + f"not {_literal(type(check_input))}"
        if raise_exception:
            raise Error("\n" + error_info)
        else:
            return error_info
    if check_input:
        type_check(iterable_, Iterable, "__iterable", False)
        type_check(type_required, (type, tuple), "type_required", False)
        if isinstance(type_required, tuple):
            for index, element in enumerate(type_required):
                type_check(element, type, f"type_required[{index}]", False)
        type_check(iterable_name, str, "__iterable_name", False)
        type_check(with_supplement, bool, "with_supplement", False)
        type_check(raise_exception, bool, "raise_exception", False)

    if len(iterable_) == 0:
        error_info = "argument 'iterable_' cannot be empty"
        if raise_exception:
            raise Error("\n" + error_info)
        else:
            return error_info
    if iterable_name == "":
        iterable_name = "_"
    for index, element in enumerate(iterable_):
        error_info = type_check(element, type_required,
                                f"{iterable_name}[{index}]", False, False)
        if error_info is not None:
            if with_supplement:
                iterable_type = _literal(type(iterable_))
                error_info += f", if a(n) {iterable_type} is given"
            break
    if raise_exception:
        raise Error("\n" + error_info)
    else:
        return error_info
