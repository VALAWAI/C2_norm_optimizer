# C2 Norm Optimizer

The Norm Optimizer is a C2 VALAWAI component that computes normative systems
that are optimal with respect to some value of interest, using off-the-shelf
metaheuristics optimizers.

Similarly to the [Alignment
Calculator](https://github.com/VALAWAI/C2_alignment_calculator), the Norm
Optimizer takes as input an arbitrary model (which in practice is implemented as
a class) with a method that defines how a set of norms governs the transition at
a time step.

To understand what the Norm Optimizer actually optimizes, it is recommended to
read first the introduction to the [Alignment
Calculator](https://github.com/VALAWAI/C2_alignment_calculator). The Norm
Optimizer simply optimizes the normative parameters in the normative system $N$
with respect to some value of interest given through its *value semantics
function*. The optimization is subject to the lower and upper bounds of the
normative parameters, as well as any potential constraints that should be taken
into account.

# Summary

 - Type: C2
 - Name: Norm Optimizer
 - Version: 1.0.0 (September 27, 2023)
 - API: [1.0.0 (October 4, 2023)](https://editor-next.swagger.io/?url=https://raw.githubusercontent.com/VALAWAI/C2_norm_optimizer/main/component-api.yml)
 - VALAWAI API: [0.1.0 (September 18, 2023)](https://editor-next.swagger.io/?url=https://raw.githubusercontent.com/VALAWAI/MOV/main/valawai-api.yml)
 - Developed by: IIIA-CSIC
 - License: [MIT](LICENSE)

# Usage

To understand how to set up and use this component, the reader is directed to
the `example.py` script available in this repository. There, you can find first
the `TaxModel` class. Read first the **Usage** section of the [Alignment
Calculator](https://github.com/VALAWAI/C2_alignment_calculator) to understand
what are the classes, methods and function defined in this script and what is
their purpose.

In the `TaxModel`, the simulation is regulated by two norms, `pay` and
`payback`. Each of these norms is attached to 5 normative parameters, `r0`, ...,
`r4`. Hence, the dictionary of normative parameters that we seek to optimize is:

```python
{'pay': ['r0', 'r1', 'r2', 'r3', 'r4'], 'payback': ['r0', 'r1', 'r2', 'r3', 'r4']}
```

For the optimization search, it is necessary to state the bounds of the
normative parameters:

```python
lower_bounds = {
    'pay': {'r0': 0.0, 'r1': 0.0, 'r2': 0.0, 'r3': 0.0, 'r4': 0.0},
    'payback': {'r0': 0.0, 'r1': 0.0, 'r2': 0.0, 'r3': 0.0, 'r4': 0.0}
}
upper__bounds = {
    'pay': {'r0': 1.0, 'r1': 1.0, 'r2': 1.0, 'r3': 1.0, 'r4': 1.0},
    'payback': {'r0': 1.0, 'r1': 1.0, 'r2': 1.0, 'r3': 1.0, 'r4': 1.0}
}
```

Finally, the last necessary step is to define constraints on the normative
parameters, if any. Mathematically, these constraints are inequalities $f_i(N)
\leq 0$, i.e. that take as input a normative system with their normative
parameters. To set up the Norm Optimizer, we define constraints as functions
that take as input a norm dictionary. For example, the following function
captures the constraints that the rates of `payback` should add up to unity:

```python
def payback_constraint(norms):
    sum_rates = sum(norms["payback"].values())
    return abs(sum_rates - 1.)
```

These constraints are added as a penalty on the fitness function used for the
optimization search.

The Alignment Calculator component is implemented as a
[Flask](https://flask.palletsprojects.com/en/2.3.x/) application. To initialize
it, use the `create_app` function:

```python
from app import create_app

app = create_app(
    YourModel,                      # your model class
    [...],                          # your model initialization arguments
    {...},                          # your model initialization keyword arguments
    norms,                          # your norms dictionary
    your_value_semantics_funcion,   # your value semantics function

    lower_bounds,                   # your lower bounds
    upper_bounds,                   # your upper bounds
    const=[payback_constraint],     # your constraints
    term_dict={"max_early_stop": 1, "epsilon": 0.01}, # termination conditions, see the MEALPY docs
    path_length=10,                 # change if needed, default is 10
    path_sample=500                 # change if needed, default is 500
)
```

To develop your own model to be deployed in a component, the `template.py`
script is provided as a blueprint.

This component communicates through the following HTTP requests:

* Data messages:

    - GET `/opt_norms`

* Control messages:

    - PATCH `/opt_cls` changes MEALPY optimizer used for the search
    - PATCH `/opt_args` changes the initialization arguments for the MEALPY
      optimizer
    - PATCH `/opt_kwargs` changes the initialization keyword arguments for the
      MEALPY optimizer
    - PATCH `/term_dict` changes the termination conditions for the optimization
      search
    - PATCH `/path_length` changes the length of the paths used to sample
      outcomes
    - PATH `/path_sample` changes the number of paths sampled to compute the
      alignment

# Deployment

Clone this repository and develop your model and value semantics functions
following the blueprint in `template.py`:

```bash
$ git clone https://github.com/VALAWAI/C2_norm_optimizer.git
```

Build your Docker image in your directory of the component repository:

```bash
$ cd /path/to/C2_norm_optimizer
$ docker build -t c2_norm_optimizer .
```

Run a Docker container with your C2 Norm Optimizer:

```bash
$ docker run --rm -d \
  --network valawai \
  --name c2_norm_optimizer \
  --mount type=bind,src="$(pwd)",target=/app \
  -p 5432:5000 \
  -e MODEL=my_model \
  c2_norm_optimizer
```

docker run --rm -d \
  --name c2_norm_optimizer \
  --mount type=bind,src="$(pwd)",target=/app \
  -p 5432:5000 \
  -e MODEL=example \
  c2_norm_optimizer

The environment variable `MODEL` refers to the script where you have defined
your model (do not include the .py extension).

Once the container is up and running, use `curl` to communicate with the
component:

```bash
$ curl http://localhost:5432/opt_norms
{
  "algn": 0.9048607793661254,
  "norms": {
    "pay": {
      "r0": 0.5477665900888846,
      "r1": 0.9386083634952787,
      "r2": 0.5055107094173359,
      "r3": 0.9499003310249331,
      "r4": 0.6815803866882211
    },
    "payback": {
      "r0": 0.03399436561190139,
      "r1": 0.3205872727529152,
      "r2": 0.21373772788216727,
      "r3": 0.3620575033734875,
      "r4": 0.1426227309170106
    }
  }
}
```

Change the MEALPY optimizer:

```bash
$ curl -X PATCH http://localhost:5432/opt_cls -d mealpy.physics_based.SA.GaussianSA
{}
```

Change the optimizer's initialization arguments:

```bash
$ curl -X PATCH http://localhost:5000/opt_args -H 'Content-Type: application/json' -d '[10000,100,0.95,0.025]'
```

Change the sample of paths used to compute the alignment:

```bash
$ curl -X PATCH http://localhost:5432/path_sample -d 200
{}
```
