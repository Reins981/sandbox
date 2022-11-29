from Shell import SshShell
from Rsi import Rsi
from Observer import Observer

class Person(Rsi, Observer):
    shell = SshShell()
    shell.open()
    @classmethod
    def spawn(cls, firstname, lastname, **attributes):
        new_class = type(lastname, (cls,), attributes)
        globals()[lastname] = new_class
        return new_class(firstname)

    def __init__(self, firstname):
        Rsi.__init__(self, Person.shell)
        Observer.__init__(self)
        print("Executing contructor of %s"%self.__class__.__name__)
        self.firstname = firstname

    def wholename(self):
        return "{} {}".format(
            self.firstname.capitalize(),
            self.__class__.__name__
        )

    def __str__(self):
        return self.firstname

def punch(self):
    print("{} ({} damage with authlevel {} and nickname {})".format(
        self.wholename(),
        self.punch_damage,
        self.authlevel,
        self.nickname
    ))

def set_input(self, m_dict):
    for key,value in m_dict.items():
        setattr(self,key,value)

if __name__ == '__main__':
    frank = Person.spawn("Frank", "Puncherson",
        punch_damage=10,
        punch=punch,
        set_input=set_input
    )

    frank.set_input({"authlevel":1, "nickname":"franknick"})
    frank.punch()
    frank.update("ARG")
    print(frank)
