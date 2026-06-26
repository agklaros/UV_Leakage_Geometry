import numpy as np

n = 0



def A(error_list):
    result = 0
    for i in range(n):
        result += (error_list[i])**-2

def S(x_list, error_list):
    return (X(x_list, error_list)**2 + Y**2 + Z**2)**0.5

def X(x_list, error_list):
    result = 0
    for i in range(n):
        result += x_list[i] / error_list[i]
    return result

def Y(y_list, error_list):
    result = 0
    for i in range(n):
        result += y_list[i] / error_list[i]
    return result

def Z(z_list, error_list):
    result = 0
    for i in range(n):
        result += z_list[i] / error_list[i]
    return result

def compChiSquared():
    return 2*(A()-S())

