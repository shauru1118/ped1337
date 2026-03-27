import argparse
import sys
from stego import generate_key, load_key, encrypt_data, decrypt_data, embed_lsb, extract_lsb, max_capacity

KEY_FILE = "key.key"

# ----------------- Команды -----------------
def keygen_command(args):
    generate_key(args.key)
    print(f"Key generated: {args.key}")


def encrypt_command(args):
    key = load_key(args.key)

    with open(args.input, "rb") as f:
        data = f.read()

    encrypted = encrypt_data(data, key)
    embed_lsb(args.image, args.output, encrypted)

    print(f"Encryption complete: {args.output}")


def decrypt_command(args):
    key = load_key(args.key)
    extracted = extract_lsb(args.image)
    decrypted = decrypt_data(extracted, key)
    sys.stdout.buffer.write(decrypted)


def capacity_command(args):
    info = max_capacity(args.image)
    print(f"Bits: {info['bits']}")
    print(f"Bytes: {info['bytes']}")
    print(f"Approx. symbols: {info['symbols']}")


# ----------------- Аргументы -----------------
def main():
    parser = argparse.ArgumentParser(description="Stego CLI with AES + adaptive LSB")

    sub = parser.add_subparsers(title="commands")

    k = sub.add_parser("keygen", help="Generate new AES key")
    k.add_argument("key", help="Path to save key file")
    k.set_defaults(func=keygen_command)

    e = sub.add_parser("encrypt", help="Encrypt file into image")
    e.add_argument("image", help="Input image (PNG/JPG)")
    e.add_argument("input", help="Input file to encrypt")
    e.add_argument("output", help="Output image file (PNG)")
    e.add_argument("key", help="AES key file")
    e.set_defaults(func=encrypt_command)

    d = sub.add_parser("decrypt", help="Decrypt data from image")
    d.add_argument("image", help="Input image (PNG)")
    d.add_argument("key", help="AES key file")
    d.set_defaults(func=decrypt_command)

    c = sub.add_parser("capacity", help="Check max capacity of image")
    c.add_argument("image", help="Input image (PNG/JPG)")
    c.set_defaults(func=capacity_command)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()