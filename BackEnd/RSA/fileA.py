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
    

def generate_large_prime(start=RANDOM_START, end=RANDOM_END):
    # generate a random number [RANDOM_START, RANDOM_END]
    num = random.randint(start,end)

    # and check whether it is prime or not
    while not is_prime(num):
        num = random.randint(start,end)

    # we know the number is prime
    return num

def generate_rsa_keys():

    # generate the first huge random prime number
    p = generate_large_prime()
    # generate the second huge random prime number
    q = generate_large_prime()

    # this is the trapdoor function: multiplying is fast but getting p and q from n is an exponentially slow operation
    n = p * q

    # Euler's  phi function
    phi = (p-1)*(q-1)

    e = random.randrange(1,phi)

    while gcd(e, phi) != 1 :
        e = random.randrange(1, phi)

    # d is the modular inverse of e
    d = modular_inverse(e, phi)[1]

    #private key and public key is
    return (d,n), (e,n)


# encrypt messages: we use public keys for encryption
def encrypt(public_key, plain_text):
    # e and n are needed for encryption (these are public)
    e, n = public_key

    # we use ASCII representations for the characters and the transformation of every character is stored in an array
    cipher_text = []

    # consider all the letters one by one and use modular exponentiation
    for char in plain_text:
        a = ord(char)
        cipher_text.append(pow(a,e,n))

    return cipher_text


#decrypt messages: we use private keys for decryption
def decrypt(private_key, cipher_text):
    # d and n are needed for decryption (these are private)
    d, n = private_key

    plain_text = ''

    for num in cipher_text:
        a =  pow(num, d, n)
        plain_text = plain_text + str(chr(a))

    return plain_text


if __name__ == '__main__':

    private_key , public_key = generate_rsa_keys()

    message = 'This is a dummy text that we will encrypt :)'
    print("Original message: %s" % message)

    cipher = encrypt(public_key, message)
    print("Cipher text: %s" % cipher)

    plain = decrypt(private_key, cipher)
    print("Decrypted text: %s" % plain)




