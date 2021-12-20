print("RSA fileA running")

import random
from math import floor
from math import sqrt

# 10^3 AND 10^5
RANDOM_START = 1e3
RANDOM_END = 1e5

def is_prime(num):

    # numbers smaller than 2 cannot be primes
    if num<2:
        return False
    
    # this is the only even prime numbers
    if num ==2:
        return True

    # other even numbers cannot be primes
    if num % 2 ==0:
        return False

    # we already have checked for numbers < 3
    # finding primes up to N we just have to check numbers up to sqrt(N)
    # increment by 2 because we have already considered even numbers
    for i in range(3,floor(sqrt(num))):
        if num % i == 0:
            return False

    return True


# Euclid's greatest common divisor algorithm: this is how we can verify
# whether (e,phi) are coprime ... with the gcd(e,phi)=1 condition
def gcd(a,b):

    while b!=0:
        a,b = b, a%b

    return a


# Extended Euclid's algorithm to find modular inverse in O(log m) so in linear time
# this is how we can find the d value which is the modular inverse of e in the RSA cryptosystem
def modular_inverse(a,b):
    
    # of course because gcd(0,b)=b and a*x+b*y - so x=0 and y=1
    if a==0:
        return b,0,1

    # so we use the Euclidean algorithm for gcd()
    # b%a is always the smaller number - and 'a' is the smaller integer always in this implementation
    div, x1, y1 = modular_inverse(b%a, a)

    #and we update the parameters for x,y accordingly
    x = y1 - (b//a)*x1
    y = x1

    # we use recursion so this is how we send the result to the previous stack frame
    return div, x, y
    
