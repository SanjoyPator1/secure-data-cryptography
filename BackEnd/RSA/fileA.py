print("RSA fileA running")

import random
from math import floor
from math import sqrt

#10^3 AND 10^5
RANDOM_START = 1e3
RANDOM_END = 1e5

def is_prime(num):

    #numbers smaller than 2 cannot be primes
    if num<2:
        return False
    
    #this is the only even prime numbers
    if num ==2:
        return True

    #other even numbers cannot be primes
    if num % 2 ==0:
        return False

    #we already have checked for numbers < 3
    #finding primes up to N we just have to check numbers up to sqrt(N)
    #increment by 2 because we have already considered even numbers
    for i in range(3,floor(sqrt(num))):
        if num % i == 0:
            return False

    return True


print(is_prime(6))
