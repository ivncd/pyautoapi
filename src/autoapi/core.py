from functools import wraps
from typing import Callable
import inspect

from fastapi import FastAPI


class AutoApi:
    def __init__(self, app : FastAPI) -> None:
        self.app = app

    def __call__(self,  method : str) -> Callable:
        def wrapper(cls):
            functions = inspect.getmembers(cls, inspect.isfunction)
            class_name = cls.__name__.lower()

            instance = cls()
            for func_name, func in functions:
                if func_name.startswith("_"):
                    continue

                func_name = func_name.lower()
                def make_endpoint(func : Callable) -> Callable:
                    @wraps(func)
                    async def endpoint(**kwargs):
                        return func(instance, **kwargs)

                    return endpoint

                endpoint = make_endpoint(func)

                # Apply function signature to endpoint
                sig = inspect.signature(func)
                params = [param for name, param in sig.parameters.items() if name != "self"]
                new_sig = inspect.Signature(parameters=params, return_annotation=sig.return_annotation)
                setattr(endpoint, "__signature__", new_sig)

                self.app.add_api_route(f"/{class_name}/{func_name}", endpoint, methods=[method])

            return cls
        
        return wrapper


app = FastAPI()
auto_api = AutoApi(app)

@auto_api("GET")
class Operations:
    def __init__(self) -> None:
        pass

    def sum(self, a : int, b : int) -> int:
        return a + b

    def multiply(self, a : int, b : int) -> int:
        return a * b

Operations()
