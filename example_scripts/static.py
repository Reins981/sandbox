#!/usr/bin/python

class A:
    @classmethod
    def _setup(cls):
        cls.usercontext_url = "https:/"
        cls.validate()
    def post(self):
        url = A._setup()
        print(url)
    @classmethod
    def validate(cls):
        print("validated")

class B(A):
    c = 3
    def __init__(self):
        self.b = 0
        super().__init__()


if __name__ == '__main__':
  
    A._setup()
