from navigation import FileNavigation
from visualisation import OpenImage


def main():
    print(FileNavigation().toFiles())
    # stop
    print(FileNavigation().buildPath())


if __name__ == "__main__":
    main()