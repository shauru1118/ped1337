import os
from funcs import encode, decode

def main():
    
    print()
    print("="*67)
    print(" "*24, "WELCOME to PED1337\n")
    print("avalible commands:")
    print("\t encode <image_path> <txt_path> <out_path>")
    print("\t decode <image_path>")
    print("\t q/exit")
    print("="*67)
    print("\n\n")

    
    while True:
        try:
    
            entered = input("ped1337 -_- > ").split(" ")
            cmd, args = entered[0], entered[1:]

            if cmd == "q" or cmd == "exit":
                break
    
            elif cmd == "encode":
                im_path, txt_path, out_path = args[:3]
                with open(txt_path, "r", encoding="utf-8") as txt_file:
                    text = txt_file.read()
                encode(im_path, text, out_path)
                print("ENCODED SUCCESSFUL")
                os.startfile(out_path)
    
            elif cmd == "decode":
                im_path, = args[:1]
                text = decode(im_path)
                print("DECODED TEXT:", text, sep="\n\n")
                with open(f"{im_path}.txt", "w", encoding="utf-8") as txt_file:
                    txt_file.write(text)
                os.startfile(f"{im_path}.txt")
    
            else:
                print("\tunknown comand")
    
        except Exception as e:
            print("ERROR:", str(e))

        
if __name__ == "__main__":
    main()

