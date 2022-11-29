#!/usr/bin/python


if __name__ == '__main__':


    def nested_items(dictionary):
        for key, value in dictionary.items():
            if type(value) is dict:
                yield nested_items(value)
            else:
                yield (key, value)

    a = {'guidance': {1: 2, 3: 4}, 
            "routing": {5: 6},
            7: 8,
            9: 10}

    def object_setup(a):
        object_setup_dict = {}
        # get the first generator object called items
        for items in nested_items(a):
            # assign values to result dict belonging to the first generator object
            if type(items) is tuple:
                object_setup_dict[items[0]] = items[1]

            else:
                # walk through the generator objects and assign all other values to result dict
                for item in items:
                    object_setup_dict[item[0]] = item[1]

        return object_setup_dict

    setup_objects = object_setup(a)
    print(setup_objects)

    print(setup_objects[1])
