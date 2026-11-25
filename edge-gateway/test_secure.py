import asyncio
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from asyncua import Client

# 1. Luodaan sertifikaatti ja avain
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "PythonEdgeGateway")])
cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
    .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
    .add_extension(x509.SubjectAlternativeName([x509.UniformResourceIdentifier("urn:python:edgegateway")]), critical=False)
    .sign(key, hashes.SHA256())
)

with open("client_cert.der", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.DER))
with open("client_key.pem", "wb") as f:
    f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))

print("Sertifikaatti luotu. Yhdistetään CODESYSiin...")

# 2. Yhdistetään salattuna
async def test():
    client = Client("opc.tcp://127.0.0.1:4840")
    client.application_uri = "urn:python:edgegateway"
    await client.set_security_string("Basic256Sha256,SignAndEncrypt,client_cert.der,client_key.pem")
    async with client:
        for dev in ["CODESYS Control Win V3 x64", "Device"]:
            nid = f"ns=4;s=|var|{dev}.Application.PLC_PRG.nTotalCount"
            try:
                val = await client.get_node(nid).read_value()
                print(f"OSUMA! Laitenimi on '{dev}', nTotalCount = {val}")
                return
            except Exception as e:
                print(f"Ei osumaa ({dev}): {type(e).__name__}")

asyncio.run(test())
