class test():
    def __init__(self):
        self.test="a"



a=test()
b=test()
c=test()

print(a.test)
print(b.test)
print(c.test)
b.test="b"
c.test="c"
print(a.test)
print(b.test)
print(c.test)

