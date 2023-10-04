from dataclasses import dataclass
from pydoc import locate
from flask import Flask, Request, jsonify, request
from mealpy.optimizer import Optimizer
from mealpy.evolutionary_based.GA import BaseGA
from traceback import format_exc
from valalgn.sampling import optimize_norms

from typing import Any, Callable, Iterable, Type

@dataclass
class NormOptimizer:
    model_cls: Type
    model_args: list[Any]
    model_kwargs: dict[str, Any]
    norms: dict[str, Iterable[str]]
    value: Callable[[object], float]
    lower_bounds: dict[str, dict[str, float]]
    upper_bounds: dict[str, dict[str, float]]
    const: Iterable[Callable[[dict[str, dict[str, float]]], float]]
    lambda_const: float
    opt_cls: type[Optimizer]
    opt_args: list[Any]
    opt_kwargs: dict[str, Any]
    term_dict: dict[str, Any]
    path_length: int
    path_sample: int

    def optimal_norms(self) -> float:
        return optimize_norms(
            self.model_cls,
            self.model_args,
            self.model_kwargs,
            self.norms,
            self.value,
            self.lower_bounds,
            self.upper_bounds,
            const=self.const,
            lambda_const=self.lambda_const,
            opt_cls=self.opt_cls,
            opt_args=self.opt_args,
            opt_kwargs=self.opt_kwargs,
            term_dict=self.term_dict,
            path_length=self.path_length,
            path_sample=self.path_sample
        )

def create_app(
    model_cls: Type,
    model_args: list[Any],
    model_kwargs: dict[str, Any],
    norms: dict[str, Iterable[str]],
    value: Callable[[object], float],
    lower_bounds: dict[str, dict[str, float]],
    upper_bounds: dict[str, dict[str, float]],
    const: Iterable[Callable[[dict[str, dict[str, float]]], float]] = [],
    lambda_const: float = 1.,
    opt_cls: type[Optimizer] = BaseGA,
    opt_args: list[Any] = [],
    opt_kwargs: dict[str, Any] = {},
    term_dict: dict[str, Any] = {"max_epoch": 100},
    path_length: int = 10,
    path_sample: int = 500,
) -> Flask:
    """Create a Flask app that optimizes norms with respect to a value.

    This C2 component of the VALAWAI architecture optimizes a set of norms with
    respect to a value (or an aggregation of values) [1]_.

    Parameters
    ----------
    model_cls : Type
        The model (e.g. an agent-based model) governed by a set of norms.
    model_args : list[Any]
        Initialization arguments for the model.
    model_kwargs : dict[str, Any]
        Initialization keyword arguments for the model.
    norms : dict[str, Iterable[str]]
        The identifies of the norms and their parameters that determine the
        evolution of the model.
    value : Callable[[object], float]
        The value semantics function with respect to whom the alignment of the
        norms is optimized.
    lower_bounds : dict[str, dict[str, float]]
        The lower bounds for the normative parameters.
    upper_bounds : dict[str, dict[str, float]]
        The upper bounds for the normative parameters.
    const : Iterable[Callable[[dict[str, dict[str, float]]], float]], optional
        Any constraints that should be respeted by the normative parameters, by
        default []. These are a set of function that take as input a norm
        dictionary and output a real number. The closer the output is to 0, the
        more respectful of the constraints is the normative system.
    lambda_const : float, optional
        The penalty to the fitness of violating the constraints, by default 1.
    opt_cls : type[Optimizer], optional
        The mealpy optimizer class used for the search, by default BaseGA.
    opt_args : list, optional
        The mealpy optimizer initialization arguments, by default [].
    opt_kwargs : dict, optional
        The mealpy optimizer initialization keyword arguments, by default [].,
        by default {}.
    term_dict : dict, optional
        The dictionary for termination condition for the optimization search, by
        default {"max_epoch": 100}. For details, see the mealpy page.
    path_length : int, optional
        The length of the evolution path used to compute the alignment, by
        default 10.
    path_sample : int, optional
        The number of paths to sample when computing the alignment, by
        default 500.

    Returns
    -------
    Flask
        A Flask application that can process GET /opt_norms requests.

    References
    ----------
    .. [1] Montes, N., & Sierra, C. (2022). Synthesis and properties of
        optimally value-aligned normative systems. Journal of Artificial
        Intelligence Research, 74, 1739–1774. https://doi.org/10.1613/jair.1.
        13487
    """

    app = Flask(__name__)
    
    optimizer = NormOptimizer(
        model_cls, model_args, model_kwargs, norms, value, lower_bounds,
        upper_bounds, const, lambda_const, opt_cls, opt_args, opt_kwargs,
        term_dict, path_length, path_sample
    )

    def __check_request(request: Request):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 415
        input_data = request.get_json()
        if not isinstance(input_data, dict):
            return {"error": f"Params must be passed as a dict"}, 400
        return input_data

    @app.get('/opt_norms')
    def get_opt_norms():
        try:
            opt_norms, algn = optimizer.optimal_norms()
            return jsonify({'norms': opt_norms, 'algn': algn}), 200
        except Exception:
            return {"error": format_exc()}, 400
        
    @app.patch('/opt_cls')
    def patch_opt_cls():
        input_data = request.get_data()
        opt_cls_str = input_data.decode()
        try:
            optimizer.opt_cls = locate(opt_cls_str)
            return {}, 200
        except Exception:
            return {"error": format_exc()}, 400
        
    @app.patch('/opt_args')
    def patch_opt_args():
        try:
            if not request.is_json:
                return {"error": "Request must be JSON"}, 415
            input_data = request.get_json()
            if not isinstance(input_data, list):
                return {"error": f"Params must be passed as a list"}, 400
            optimizer.opt_args = input_data
            return {}, 200
        except Exception:
            return {"error": format_exc()}, 400
        
    @app.patch('/opt_kwargs')
    def patch_opt_kwargs():
        try:
            opt_kwargs = __check_request(request)
            optimizer.opt_kwargs = opt_kwargs
            return {}, 200
        except Exception:
            return {"error": format_exc()}, 400

    @app.patch('/term_dict')
    def patch_term_dict():
        try:
            term_dict = __check_request(request)
            optimizer.term_dict = term_dict
            return {}, 200
        except Exception:
            return {"error": format_exc()}, 400

    @app.patch('/path_length')
    def patch_path_length():
        input_data = request.get_data()
        try:
            optimizer.path_length = int(input_data)
            return {}, 200
        except Exception:
            return {"error": format_exc()}, 400
        
    @app.patch('/path_sample')
    def patch_path_sample():
        input_data = request.get_data()
        try:
            optimizer.path_sample = int(input_data)
            return {}, 200
        except Exception:
            return {"error": format_exc()}, 400
        
    return app
