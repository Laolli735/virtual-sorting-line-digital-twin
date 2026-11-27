import asyncio
import datetime
import ipaddress
import socket
import os
import random
import secrets
from pathlib import Path

from asyncua import Server, ua
from asyncua.server.user_managers import CertificateUserManager
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

SERVER_CERT = Path(__file__).parent / "server_cert.der"
SERVER_KEY = Path(__file__).parent / "server_key.pem"
CLIENT_CERT = ROOT_DIR / "client_cert.der"

OPCUA_ENDPOINT = os.getenv("SIM_OPCUA_URL", "opc.tcp://0.0.0.0:4841")
PREFIX = "|var|CODESYS Control Win V3 x64.Application.PLC_PRG"


def ensure_server_certificates() -> None:
    """Generate a self-signed OPC UA server certificate if missing."""
    if SERVER_CERT.exists() and SERVER_KEY.exists():
        return

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "PythonVirtualPLC"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "VirtualSortingLine"),
    ])
    serial = secrets.randbits(127) | 1

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(serial)
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,
                key_encipherment=True,
                data_encipherment=True,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH, ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
        .add_extension(
            x509.SubjectAlternativeName([
                x509.UniformResourceIdentifier("urn:python:virtualplc"),
                x509.DNSName("localhost"), x509.DNSName(socket.gethostname()),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    SERVER_KEY.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    SERVER_CERT.write_bytes(cert.public_bytes(serialization.Encoding.DER))
    print("Generated OPC UA simulator server certificate.")


class SortingLineSimulator:
    """In-memory physics and state machine replicating CODESYS PLC_PRG."""

    def __init__(self) -> None:
        self.system_state: int = 0  # 0=IDLE, 10=RUN, 99=FAULT
        self.conveyor_running: bool = False
        self.total_count: int = 0
        self.sorted_a_count: int = 0
        self.sorted_b_count: int = 0
        self._tick_counter: int = 0

    def step(
        self,
        cmd_start: bool,
        cmd_stop: bool,
        cmd_reset: bool,
        sim_fault: bool,
    ) -> dict[str, int | bool]:
        # Fault overrides everything
        if sim_fault:
            self.system_state = 99
            self.conveyor_running = False
        elif self.system_state == 99:
            if cmd_reset:
                self.system_state = 0
                self.conveyor_running = False
        else:
            if cmd_stop:
                self.system_state = 0
                self.conveyor_running = False
            elif cmd_start:
                self.system_state = 10
                self.conveyor_running = True

        # Simulate optical sorting every 3 ticks (1.5s at 0.5s cycle) when running
        if self.system_state == 10 and self.conveyor_running:
            self._tick_counter += 1
            if self._tick_counter >= 3:
                self._tick_counter = 0
                self.total_count += 1
                if random.random() < 0.55:
                    self.sorted_a_count += 1
                else:
                    self.sorted_b_count += 1
        else:
            self._tick_counter = 0

        return {
            "nSystemState": self.system_state,
            "bConveyorMain": self.conveyor_running,
            "nTotalCount": self.total_count,
            "nSortedACount": self.sorted_a_count,
            "nSortedBCount": self.sorted_b_count,
        }


async def run_simulator() -> None:
    ensure_server_certificates()

    cert_user_manager = CertificateUserManager()
    if CLIENT_CERT.exists():
        await cert_user_manager.add_user(str(CLIENT_CERT), "edge_gateway")

    server = Server(user_manager=cert_user_manager)
    await server.init()
    server.set_endpoint(OPCUA_ENDPOINT)
    server.set_server_name("Virtual Sorting Line OPC UA PLC Simulator")
    await server.set_application_uri("urn:python:virtualplc")

    server.set_security_policy(
        [ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt],
    )
    await server.load_certificate(str(SERVER_CERT))
    await server.load_private_key(str(SERVER_KEY))

    # Register namespaces so custom PLC tags reside in ns=4 (matching CODESYS)
    await server.register_namespace("http://opcfoundation.org/UA/PLC/")
    await server.register_namespace("urn:CODESYS:Server")
    ns_idx = await server.register_namespace("urn:CODESYS:Application")

    objects = server.nodes.objects
    plc_folder = await objects.add_folder(f"ns={ns_idx};s={PREFIX}", "PLC_PRG")

    tags = {
        "nSystemState": await plc_folder.add_variable(
            f"ns={ns_idx};s={PREFIX}.nSystemState", "nSystemState", ua.Variant(0, ua.VariantType.Int16)
        ),
        "bConveyorMain": await plc_folder.add_variable(
            f"ns={ns_idx};s={PREFIX}.bConveyorMain", "bConveyorMain", ua.Variant(False, ua.VariantType.Boolean)
        ),
        "nTotalCount": await plc_folder.add_variable(
            f"ns={ns_idx};s={PREFIX}.nTotalCount", "nTotalCount", ua.Variant(0, ua.VariantType.Int32)
        ),
        "nSortedACount": await plc_folder.add_variable(
            f"ns={ns_idx};s={PREFIX}.nSortedACount", "nSortedACount", ua.Variant(0, ua.VariantType.Int32)
        ),
        "nSortedBCount": await plc_folder.add_variable(
            f"ns={ns_idx};s={PREFIX}.nSortedBCount", "nSortedBCount", ua.Variant(0, ua.VariantType.Int32)
        ),
        "bCmdStart": await plc_folder.add_variable(
            f"ns={ns_idx};s={PREFIX}.bCmdStart", "bCmdStart", ua.Variant(False, ua.VariantType.Boolean)
        ),
        "bCmdStop": await plc_folder.add_variable(
            f"ns={ns_idx};s={PREFIX}.bCmdStop", "bCmdStop", ua.Variant(False, ua.VariantType.Boolean)
        ),
        "bCmdReset": await plc_folder.add_variable(
            f"ns={ns_idx};s={PREFIX}.bCmdReset", "bCmdReset", ua.Variant(False, ua.VariantType.Boolean)
        ),
        "bSimFault": await plc_folder.add_variable(
            f"ns={ns_idx};s={PREFIX}.bSimFault", "bSimFault", ua.Variant(False, ua.VariantType.Boolean)
        ),
    }

    for cmd_key in ("bCmdStart", "bCmdStop", "bCmdReset", "bSimFault"):
        await tags[cmd_key].set_writable()

    sim = SortingLineSimulator()
    print(f"Virtual PLC OPC UA Server listening on {OPCUA_ENDPOINT} (ns={ns_idx})")

    async with server:
        while True:
            cmd_start = bool(await tags["bCmdStart"].read_value())
            cmd_stop = bool(await tags["bCmdStop"].read_value())
            cmd_reset = bool(await tags["bCmdReset"].read_value())
            sim_fault = bool(await tags["bSimFault"].read_value())

            # Clear momentary HMI command pulses
            if cmd_start:
                await tags["bCmdStart"].write_value(False)
            if cmd_stop:
                await tags["bCmdStop"].write_value(False)
            if cmd_reset:
                await tags["bCmdReset"].write_value(False)
            if sim_fault:
                await tags["bSimFault"].write_value(False)

            state = sim.step(cmd_start, cmd_stop, cmd_reset, sim_fault)

            await tags["nSystemState"].write_value(ua.Variant(state["nSystemState"], ua.VariantType.Int16))
            await tags["bConveyorMain"].write_value(ua.Variant(state["bConveyorMain"], ua.VariantType.Boolean))
            await tags["nTotalCount"].write_value(ua.Variant(state["nTotalCount"], ua.VariantType.Int32))
            await tags["nSortedACount"].write_value(ua.Variant(state["nSortedACount"], ua.VariantType.Int32))
            await tags["nSortedBCount"].write_value(ua.Variant(state["nSortedBCount"], ua.VariantType.Int32))

            await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(run_simulator())