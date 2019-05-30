import math


def sigmoid(x, slope=1, bound=1):
    return  1 + bound * (2 / (1 + math.exp(-2*slope*(x-1)/bound)) - 1) if bound else 1


def log(x, default=0, *args, **kwargs):
    return math.log(x, *args, **kwargs) if x > 0 else default