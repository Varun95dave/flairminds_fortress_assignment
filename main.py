import sys
import Transformer



def main(args):

    import sys

    data_transform = Transformer.Transformer()
    data_transform.transform()
    sys.exit()

def run():

    main(sys.argv[1:])

if __name__  == "__main__":
    run()