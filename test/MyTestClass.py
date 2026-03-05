class MyTestClass:
    outside = 1

    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}!"
    
class ChildClass(MyTestClass):
    def __init__(self, name, age):
        super().__init__(name)
        self.age = age

if __name__ == "__main__":
    test_instance = MyTestClass("Alice")
    print(test_instance.greet())
    print(f"Outside variable: {MyTestClass.outside}")
    test_instance.name = "Bob"
    print(test_instance.greet())
    print(f"Modified outside variable: {test_instance.outside}")
    print(f"Class variable outside: {MyTestClass.outside}")
    child_instance = ChildClass("Charlie", 30)
    print(child_instance.greet())
    print(f"Child's age: {child_instance.age}")
    print(f"Child's outside variable: {child_instance.outside}")
    MyTestClass.outside = 3
    print(f"Modified class variable outside: {MyTestClass.outside}")
    print(f"Child's outside variable after class modification: {ChildClass.outside}")
    print(f"Child's outside variable after modification: {child_instance.outside}")
    print(f"Test instance's outside variable after modification: {test_instance.outside}")