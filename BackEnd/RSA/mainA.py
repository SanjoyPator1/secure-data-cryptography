from flask import Flask
import fileA as rsa





app = Flask(__name__)

@app.route('/rsa')
# ‘/rsa’ URL
def fun2():
    private_key, public_key = rsa.generate_rsa_keys()

    message = 'This is a dummy text that we will encrypt :)'
    print("Original message: %s" % message)

    cipher = rsa.encrypt(public_key, message)
    print("Cipher text: %s" % cipher)

    plain = rsa.decrypt(private_key, cipher)
    print("Decrypted text: %s" % plain)
    return plain


# main driver function
if __name__ == '__main__':
    app.run()
