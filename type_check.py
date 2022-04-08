from functools import wraps
from typing import Iterable, Union

__author__ = "Lingxuan Ye"
__version__ = "1.2.4"
__all__ = ["type_check", "element_type_check"]


def _raise(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        result: dict = func(*args, **kwargs)
        if not isinstance(result, dict):
            return result
        raise_exception = result.get("raise_exception", False)
        error_info = result.get("error_info", None)
        if (raise_exception == True) and (error_info is not None):
            raise TypeError(error_info)
        return result

    return wrapper


def _literal(__type: type, enclosed_with_quotes: bool = True):
    type_literal = str(__type).split("'")[1]
    if enclosed_with_quotes:
        return "'" + type_literal + "'"
    else:
        return type_literal


@_raise
def type_check(arg,
               type_required: Union[type, tuple],
               arg_name: str,
               check_input: bool = True,
               raise_exception: bool = True):
    """
    If the argument 'check_input' is set to True,
    function 'type_check' will check whether its arguments
    are valid.

    If the argument 'raise_exception' is set to False,
    function 'type_check' will return a dict in which
    the information of error occurred can be found from key 'error_info'.

    If the argument 'raise_exception' is set to True,
    function 'type_check' will raise exception if type check fails.
    """
    result = {"raise_exception": raise_exception, "error_info": None}

    if not isinstance(check_input, bool):
        error_info = "argument 'check_input' must be 'bool', " \
                   + f"not {_literal(type(check_input))}"
        result["error_info"] = error_info
        return result
    if check_input:
        type_check(type_required, (type, tuple), "type_required", False)
        if isinstance(type_required, tuple):
            for index, element in enumerate(type_required):
                type_check(element, type, f"type_required[{index}]", False)
        type_check(arg_name, str, "arg_name", False)
        type_check(raise_exception, bool, "raise_exception", False)

    if isinstance(arg, type_required):
        return result
    if isinstance(type_required, tuple):
        if len(type_required) == 0:
            error_info = "argument 'type_required' cannot be empty, " \
                       + "if a 'tuple' is given"
            result["error_info"] = error_info
            return result
        type_list = []
        for type_ in type_required:
            type_list.append(_literal(type_))
        type_info = ", ".join(type_list[0:-1]) + f" or {type_list[-1]}"
    else:  # isinstance(type_required, type) == True
        type_info = _literal(type_required)
    error_info = f"argument '{arg_name}' must be {type_info}, " \
               + f"not {_literal(type(arg))}"
    result["error_info"] = error_info
    return result


@_raise
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
    function 'element_type_check' will return a dict in which
    the information of error occurred can be found from key 'error_info'.

    If the argument 'raise_exception' is set to True,
    function 'element_type_check' will raise exception if type check fails.
    """
    result = {"raise_exception": raise_exception, "error_info": None}

    if not isinstance(check_input, bool):
        error_info = "argument 'check_input' must be 'bool', " \
                   + f"not {_literal(type(check_input))}"
        result["error_info"] = error_info
        return result
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
        result["error_info"] = error_info
        return result
    if iterable_name == "":
        iterable_name = "_"
    for index, element in enumerate(iterable_):
        _result = type_check(element, type_required,
                             f"{iterable_name}[{index}]", False, False)
        error_info = _result["error_info"]
        if error_info is not None:
            if with_supplement:
                iterable_type = _literal(type(iterable_))
                error_info += f", if a(n) {iterable_type} is given"
            break
    result["error_info"] = error_info
    return result
