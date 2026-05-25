from itertools import product
from collections import defaultdict

#define what can happen (sample space
# define what we're looking for (event condition)
#count how many ways to get it
#divide by total number of possiblities

toys = ['Car', 'Doll', 'Ball', 'Puzzle']
sample_space = set(product(toys, repeat=5))

print(f"Total combinations: {len(sample_space)}")

first_combination = list(sample_space)[0]
print(first_combination)

#event condition first bag is a car
def first_bag_is_car(outcome):
    return outcome[0] == 'Car'
#count manualy understand what we're counting
matching = [outcome for outcome in sample_space if first_bag_is_car(outcome)]

print(f"comginations where fist bag is a car: {len(matching)}")
print(f"probability: {len(matching) / len(sample_space)}")

def all_bags_are_dolls(outcome):
    return all(toy == 'Doll' for toy in outcome)

matching = [outcome for outcome in sample_space if all_bags_are_dolls(outcome)]

print(f"combinations where all bags are dolls: {len(matching)}")
print(f"probability: {len(matching) / len(sample_space)}")

#event condition 
def has_at_least_3_balls(outcome):
    return outcome.count('Ball') >= 3

matching = [outcome for outcome in sample_space if has_at_least_3_balls(outcome)]

print(f"combinations where at least 3 bags are balls: {len(matching)}")
print(f"probability: {len(matching) / len(sample_space)}")

#your probability function can reuse
def compute_event_probability(event_conddition, generic_sample_space):
    event = get_matching_event(event_conddition, generic_sample_space)
    if type(generic_sample_space) == type(set()):
        return len(event) / len(generic_sample_space)
    event_size = sum(generic_sample_space[outcome] for outcome in event)
    return event_size / sum(generic_sample_space.values())

