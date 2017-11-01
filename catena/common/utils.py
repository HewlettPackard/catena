# (C) Copyright 2017 Hewlett Packard Enterprise Development LP.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from binascii import b2a_base64
import datetime

from Crypto.Cipher import AES
from Crypto.Hash import MD5
from Crypto.Protocol.KDF import PBKDF1
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Util.Padding import pad
from Crypto.Util.py3compat import hexlify
from Crypto.Util.py3compat import tostr
import iso8601
from oslo_config import cfg

CONF = cfg.CONF


def utcnow(with_timezone=False):
    """Overridable version of utils.utcnow that can return a TZ-aware datetime.
    """
    if utcnow.override_time:
        try:
            return utcnow.override_time.pop(0)
        except AttributeError:
            return utcnow.override_time
    if with_timezone:
        return datetime.datetime.now(tz=iso8601.iso8601.UTC)
    return datetime.datetime.utcnow()


def encrypt_private_rsakey(key):
    private_key = RSA.import_key(key)
    return encrypt_key_object(private_key)


def encrypt_key_object(private_key):
    data = private_key.exportKey(format='DER')
    out = "-----BEGIN RSA PRIVATE KEY-----\n"
    salt = Random.get_random_bytes(16)

    # Doing some AES-128-CBC here
    key = PBKDF1(CONF.get('encryption_key'), salt[:8], 16, 1, MD5)
    objenc = AES.new(key, AES.MODE_CBC, salt)

    out += "Proc-Type: 4,ENCRYPTED\nDEK-Info: AES-128-CBC,%s\n\n" % (
        tostr(hexlify(salt).upper()))

    data = objenc.encrypt(pad(data, objenc.block_size))
    chunks = [tostr(b2a_base64(data[i:i + 48])) for i in
              range(0, len(data), 48)]
    out += "".join(chunks)
    out += "-----END RSA PRIVATE KEY-----"

    return out


def create_and_encrypt_sshkey():
    keypair = RSA.generate(2048)

    public_key = keypair.exportKey('OpenSSH')
    private_key = encrypt_key_object(keypair)

    return public_key, private_key


def decrypt_rsakey(key):
    private_key = RSA.import_key(key, CONF.get('encryption_key'))
    return private_key.exportKey()


def decrypt_private_rsakey(key, file):
    file.write(decrypt_rsakey(key))
    file.flush()


utcnow.override_time = None
