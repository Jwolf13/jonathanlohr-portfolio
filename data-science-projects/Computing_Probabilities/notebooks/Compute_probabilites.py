from itertools import product
from collections import defaultdict
# Real-World Data (Empirical)
#mport pandas as pd

# 1. Ingest from an external source (e.g., a CSV file of actual dice rolled at a casino)
#casino_data = pd.read_csv('`actual_dice_rolls.csv`')

# 2. Clean it (e.g., remove rows where the dice fell off the table)
#clean_data = casino_data.dropna()

# 3. Turn it into your sample space!
# Let's say the CSV has a column called 'Roll_Result'
#sample_space = list(clean_data['Roll_Result'])

# 4. Use the EXACT same functions you already wrote!

sample_space = {'Heads', 'Tails'}
#sample space of coin flips, this is a dictionary of the possible outcomes of a coin flip, we can use this to compute probabilities of events related to coin flips

probability_heads = 1/ len(sample_space)
#compute the probability of getting heads
print(f"The probability of getting heads is: {probability_heads}")
# this creates a dictionary of the sample space and then computes the probability of getting heads by dividing 1 by the number of outcomes in the sample space

def is_heads_or_tails(outcome): 
    return outcome in {'Heads', 'Tails'}
#function to check if an outcome is heads or tails so this creates a dictionary of the outcomes that a
def is_neither(outcome):
    return not is_heads_or_tails(outcome)
#function to check if an outcome is neither heads nor tails, How am I using this? 

def is_heads(outcome):
    return outcome == 'Heads'
#function to check if an outcome is heads
def is_tails(outcome):
    return outcome == 'Tails'
#function to check if an outcome is tails

def get_matching_event(event_condition, generic_sample_space):
    return set([outcome for outcome in generic_sample_space
                if event_condition(outcome)])
#function to get the matching event from a generic sample space based on a given event condition
# this creates a for loop that iterates through the generic sample space and checks if each outcome matches the event condition, if it does it adds it to a set of outcomes that match the event condition

event_conditions = [is_heads_or_tails, is_heads, is_tails, is_neither]
# this is a list of the event conditions we want to check against the sample space, The above functions are the event conditions we want to check against the sample space, we can use these functions to compute the probabilities of different events related to coin flips

for event_condition in event_conditions: 
    print(f"Event Condition: {event_condition.__name__}")
    event = get_matching_event(event_condition, sample_space)
    print(f'Event: {event}\n')

def compute_probability(event_condition, generic_sample_space):
    event = get_matching_event(event_condition, generic_sample_space)
    return len(event) / len(generic_sample_space)

for event_condition in event_conditions: 
    prob = compute_probability(event_condition, sample_space)
    name = event_condition.__name__
    print(f"Probability of event arising from '{name}' is {prob}")

weighted_sample_space = {'Heads': 4, 'Tails': 1}

sample_space_size = sum(weighted_sample_space.values())
assert sample_space_size == 5

event = get_matching_event(is_heads_or_tails, weighted_sample_space)
event_size = sum(weighted_sample_space[outcome] for outcome in event)
assert event_size == 5

def compute_event_probability(event_condition, generic_sample_space):
    event = get_matching_event(event_condition, generic_sample_space)
    if type(generic_sample_space) == type(set()):
        return len(event) / len(generic_sample_space)
    
    event_size = sum(generic_sample_space[outcome]
                     for outcome in event)
    return event_size / sum(generic_sample_space.values())

#we can now output all the event probabilites fo rthe biased coin without redining event dondition fucntions

for event_condition in event_conditions: 
    prob = compute_event_probability(event_condition, weighted_sample_space)
    name = event_condition.__name__
    print(f"probability of event arising from '{name}' is {prob}\n")


possible_children = ['Boy', 'Girl']
sample_space = set()
for child in possible_children:
    for child2 in possible_children:
        for child3 in possible_children:
            for child4 in possible_children:
                outcome = (child, child2, child3, child4)
                sample_space.add(outcome)

sample_space_efficient = set(product(possible_children, repeat=4))
assert sample_space == sample_space_efficient

def has_two_boys(outcome):
    return len([child for child in outcome 
                if child == 'Boy']) == 2

prob = compute_event_probability(has_two_boys, sample_space)
print(f"The probability 2 boys is {prob}")

possible_rolls = list(range(1, 7))
print(f"Possible rolls: {possible_rolls}")

#sample space for 6 consecutive die rolls
sample_space = set(product(possible_rolls, repeat=6))

def has_sum_of_21(outcome):
    return sum(outcome) == 21

prob = compute_event_probability(has_sum_of_21, sample_space)
print(f"6 rolls sum to 21 with a probability of {prob}")

prob = compute_event_probability(lambda x: sum(x) == 21, sample_space)
assert prob == compute_event_probability(has_sum_of_21, sample_space)

weighted_sample_space = defaultdict(int)
for outcome in sample_space:
    total = sum(outcome)
    weighted_sample_space[total] += 1

assert weighted_sample_space[6] == 1
assert weighted_sample_space[36] == 1

num_combinations = weighted_sample_space[21]
print(f"there are {num_combinations} ways for 6 rolls to sum to 21")

assert sum([4,4,4,4,3,2]) == 21
assert sum([4,4,4,5,3,1]) == 21

event = get_matching_event(lambda x: sum(x) == 21, sample_space)
assert weighted_sample_space[21] == len(event)
assert sum(weighted_sample_space.values()) == len(sample_space)

prob = compute_event_probability(lambda x: x == 21, weighted_sample_space)
assert prob == compute_event_probability(has_sum_of_21, sample_space)
print(f"the probability of 6 rolls summing to 21 is {prob}")

print('number of elements in unweighted sample space:', len(sample_space))
print('number of elements in weighted sample space:', len(weighted_sample_space))
