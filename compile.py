import argparse
import os
import shutil


def compile_script(folderName):
    icon = "lingualeo.ico"
    name = "Kindleo"
    scriptName = "gui_export.py"
    command = "pyinstaller -noconsole -F --icon={0} --name={1} "\
              "--distpath={2} {3}".format(icon,
                                          name,
                                          folderName,
                                          scriptName)
    os.system(command)
    print("Compiled to {}".format(folderName))


def copytree(src, dst):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, src, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            # to ignore src.ini
            continue
    print("Copied src folder")


def zip(folder):
    shutil.make_archive(folder, "zip", folder)
    print("Created {} archive".format(folder))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument("system")
    args = parser.parse_args()
    version = args.version
    system = "lin" if "lin" in args.system else "win"
    name = "Kindleo_{}_{}".format(version, system)

    compile_script(name)

    copytree("src", name)

    shutil.make_archive(name, "zip", name)

if __name__ == "__main__":
    main()
