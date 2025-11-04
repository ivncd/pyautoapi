from functools import wraps
from typing import Callable
import inspect

from fastapi import FastAPI


class AutoApi:
    def __init__(self, app : FastAPI) -> None:
        self.app = app
        self.added_cls = []

    def __call__(self,  method : str) -> Callable:
        def wrapper(cls):
            if not inspect.isclass(cls):
                raise ValueError("The decorator should only be added to a class")

            class_name = cls.__name__.lower()
            if class_name in self.added_cls:
                print(f"The class {cls.__name__} has already been initialized by another one")
                return cls

            self.added_cls.append(class_name)
            functions = [(name, member) for name, member in inspect.getmembers(cls) if callable(member)]
            instance = cls()
            for func_name, func in functions:
                if func_name.startswith("_") or getattr(func, "_autoapi_ignore", False):
                    continue

                func_name = func_name.lower()
                def make_endpoint(func : Callable, is_static : bool, is_classmethod : bool) -> Callable:
                    @wraps(func)
                    async def endpoint(**kwargs):
                        if is_static or is_classmethod:
                            return func(**kwargs)

                        return func(instance, **kwargs)

                    return endpoint

                unwrapped_func = cls.__dict__.get(func_name)
                is_static = isinstance(unwrapped_func, staticmethod) 
                is_classmethod = isinstance(unwrapped_func, classmethod) 
                endpoint = make_endpoint(func, is_static, is_classmethod)

                # Apply function signature to endpoint
                sig = inspect.signature(func)
                items = list(sig.parameters.values())[1:] if not(is_static or is_classmethod) else list(sig.parameters.values())
                params = [param for param in items]
                new_sig = inspect.Signature(parameters=params, return_annotation=sig.return_annotation)
                setattr(endpoint, "__signature__", new_sig)

                self.app.add_api_route(f"/{class_name}/{func_name}", endpoint, methods=[method])

            return cls
        
        return wrapper

    def ignore(self, func):
        target = func
        if not(inspect.isfunction(func) or isinstance(func, (classmethod, staticmethod))):
            raise ValueError(f"Ignore expects a function but a {type(func)} was given")

        if isinstance(func, (classmethod, staticmethod)):
            target = func.__func__

        setattr(target, "_autoapi_ignore", True)
        return func

app = FastAPI()
auto_api = AutoApi(app)

@auto_api("GET")
class Operations:
    counter = 0
    def __init__(self) -> None:
        pass
    
    def sum(self, a : int, b : int) -> int:
        return a + b

    @staticmethod
    def multiply(a : int, b : int) -> int:
        return a * b
    
    @classmethod
    def count(cls) -> int:
        cls.counter += 1
        return cls.counter
    

    @auto_api.ignore
    def ignored(self) -> int:
        return 0
