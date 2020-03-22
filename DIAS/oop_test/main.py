
class A:

    a = 1
    def __init__(self):
        pass
class B(A):

    b  = None
    def __init__(self,b):
        super().__init__()
        self.b = b

class C(B):
    def __init__(self):
        super().__init__(1)

    def test(self):
        print(super().a)

if __name__ == '__main__':

    c = C()
    print(c.b)