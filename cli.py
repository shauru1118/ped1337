import argparse
import sys
from abc import ABC, abstractmethod
from typing import Dict
from stego import StegoFacade, StegoError


class ICLICommand(ABC):
    """Command Pattern interface for CLI command handlers."""

    @abstractmethod
    def execute(self, args: argparse.Namespace, facade: StegoFacade) -> None:
        pass


class KeygenCommand(ICLICommand):
    """Command handler for key generation."""

    def execute(self, args: argparse.Namespace, facade: StegoFacade) -> None:
        facade.generate_key_file(args.key)
        print(f"Key generated successfully: {args.key}")


class EncryptCommand(ICLICommand):
    """Command handler for encrypting and embedding a file into an image."""

    def execute(self, args: argparse.Namespace, facade: StegoFacade) -> None:
        key = facade.load_key(args.key)
        with open(args.input, "rb") as f:
            data = f.read()

        facade.embed_encrypted(args.image, args.output, data, key)
        print(f"Encryption and embedding complete: {args.output}")


class DecryptCommand(ICLICommand):
    """Command handler for extracting and decrypting data from an image."""

    def execute(self, args: argparse.Namespace, facade: StegoFacade) -> None:
        key = facade.load_key(args.key)
        decrypted_data = facade.extract_decrypted(args.image, key)
        sys.stdout.buffer.write(decrypted_data)


class CapacityCommand(ICLICommand):
    """Command handler for calculating maximum embedding capacity."""

    def execute(self, args: argparse.Namespace, facade: StegoFacade) -> None:
        info = facade.calculate_capacity(args.image)
        print(f"Bits: {info['bits']}")
        print(f"Bytes: {info['bytes']}")
        print(f"Approx. symbols: {info['symbols']}")


class StegoCLIApplication:
    """Invoker class managing command dispatching and execution."""

    def __init__(self):
        self.facade = StegoFacade()
        self._commands: Dict[str, ICLICommand] = {
            "keygen": KeygenCommand(),
            "encrypt": EncryptCommand(),
            "decrypt": DecryptCommand(),
            "capacity": CapacityCommand(),
        }

    def build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description=(
                "Steganography CLI (Kuznyechik CBC + GOST MAC + Zlib + Adaptive LSB)"
            )
        )
        subparsers = parser.add_subparsers(
            title="commands", dest="command", required=True
        )

        k = subparsers.add_parser("keygen", help="Generate a new 256-bit key")
        k.add_argument("key", help="Path to save key file")

        e = subparsers.add_parser("encrypt", help="Encrypt and embed file into image")
        e.add_argument("image", help="Input cover image (PNG/JPG)")
        e.add_argument("input", help="Input file to encrypt and hide")
        e.add_argument("output", help="Output stego image file (PNG)")
        e.add_argument("key", help="Key file path")

        d = subparsers.add_parser(
            "decrypt", help="Extract and decrypt data from stego image"
        )
        d.add_argument("image", help="Input stego image (PNG)")
        d.add_argument("key", help="Key file path")
        c = subparsers.add_parser(
            "capacity", help="Check maximum embedding capacity of an image"
        )
        c.add_argument("image", help="Input image path (PNG/JPG)")

        return parser

    def run(self, args_list: list = None) -> None:
        parser = self.build_parser()
        try:
            args = parser.parse_args(args_list)
            command = self._commands.get(args.command)
            if command:
                command.execute(args, self.facade)
            else:
                parser.print_help()
        except StegoError as e:
            print(f"Stego Domain Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected Error: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    app = StegoCLIApplication()
    app.run()


if __name__ == "__main__":
    main()