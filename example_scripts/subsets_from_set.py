#!/usr/bin/python


def all_subsets(given_array):
    subset = [None]*len(given_array)
    helper(given_array, subset, 0)


def helper(given_array, subset, i):
    if i == len(given_array):
        print(str(subset))
    else:
        subset[i] = None
        helper(given_array, subset, i+1)
        print('This value has been removed from first stack %s' %str(i))
        subset[i] = given_array[i]
        helper(given_array, subset, i+1)
        print('This value has been removed from second stack %s' %str(i))


if __name__ == '__main__':
    a = [1,2]
    all_subsets(a)
