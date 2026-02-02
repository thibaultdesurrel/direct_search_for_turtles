class FunctionGenerator():
    """
    Is an object that can generate functions 1D and 2D.
    """

    #TODO: I let you do your math magic here

    def __init__(self,dim:int):
        self.dim = dim

    def generate(self):
        return lambda x: x # dummy function


if __name__ == "__main__":
    # Here entry point of the function
    # use python src/server/game/function_generator.py to exectute the code in here
    fg = FunctionGenerator(1)
    f.generate()