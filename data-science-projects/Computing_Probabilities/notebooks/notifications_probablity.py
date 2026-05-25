from itertools import product
from collections import defaultdict

my_notifications = (
    ['Message'] * 5 +
    ['Social'] * 3 +
    ['Email'] * 20 +
    ['Spam'] * 20 +
    ['System'] * 4
)

print(f"Total notifications: {len(my_notifications)}")
print(f"\nBreakdown:")
print(f"Messages: {my_notifications.count('Message')}")
print(f"Social: {my_notifications.count('Social')}")
print(f"Email: {my_notifications.count('Email')}")
print(f"Spam: {my_notifications.count('Spam')}")
print(f"System: {my_notifications.count('System')}")

def is_worth_checking(notification):
    return notification == 'Message'

#calculate probability of receiving a message
good_notifications = [n for n in my_notifications if is_worth_checking(n)]
prob_good = len(good_notifications) / len(my_notifications)

print(f"\nProbability notification is worth checking: {prob_good:.2%}")
print(f"That's {len(good_notifications)} out of {len(my_notifications)}")

#cost-benefit-analysis
context_switch_cost = 5 
urgent_message_value = 10

expected_value = (prob_good * urgent_message_value) - (1 - prob_good) * context_switch_cost

print(f"\nExpected value of checking: {expected_value:.2f}")

from itertools import product

# Sample space: all possible sequences of 3 notifications
notification_types = ['Message', 'Social', 'Email', 'Spam', 'System']

# Weighted by YOUR actual frequencies
weighted_sample_space = {
    'Message': 100,
    'Social': 4,
    'Email': 20,
    'Spam': 20,
    'System': 4
}

# Total weight
total_weight = sum(weighted_sample_space.values())  # 52

# Probability ONE notification is spam
prob_one_spam = weighted_sample_space['Spam'] / total_weight
print(f"Probability one notification is spam: {prob_one_spam:.2%}")

# Probability THREE in a row are spam (independent events)
prob_three_spam = prob_one_spam ** 3
print(f"Probability three consecutive notifications are spam: {prob_three_spam:.2%}")

from itertools import product
from collections import defaultdict

def generate_notification_sample_space(num_notifications=52):
    """
    Generate weighted sample space for notification counts
    Based on YOUR actual distribution
    """
    # Your notification types with their weights
    notification_types = ['Message', 'Social', 'Email', 'Spam', 'System']
    weights = {
        'Message': 5,
        'Social': 3, 
        'Email': 20,
        'Spam': 20,
        'System': 4
    }
    
    weighted_sample_space = defaultdict(int)
    
    # This would be HUGE (5^52 combinations), so we'll use probability instead
    # But let's demonstrate with a smaller example first
    
    return weighted_sample_space

# Let's start smaller - 10 notifications instead of 52
def generate_small_notification_space(num_notifications=10):
    notification_types = ['Message', 'Noise']  # Simplified
    
    weighted_sample_space = defaultdict(int)
    
    for outcome in product(notification_types, repeat=num_notifications):
        message_count = outcome.count('Message')
        weighted_sample_space[message_count] += 1
    
    return weighted_sample_space

small_space = generate_small_notification_space(10)

print("Message Count : Number of Ways to Get It")
for count in sorted(small_space.keys()):
    print(f"{count:3d} messages : {small_space[count]:4d} ways")


def is_in_interval(number, minimum, maximum):
    return minimum <= number <= maximum

def compute_event_probability(event_condition, generic_sample_space):
    event = {outcome for outcome in generic_sample_space 
             if event_condition(outcome)}
    
    if isinstance(generic_sample_space, set):
        return len(event) / len(generic_sample_space)
    
    # Weighted version
    event_size = sum(generic_sample_space[outcome] for outcome in event)
    return event_size / sum(generic_sample_space.values())

# Probability of "normal" range (3-7 messages out of 10)
prob_normal = compute_event_probability(
    lambda x: is_in_interval(x, 3, 7),
    small_space
)

print(f"\nProbability of 3-7 messages: {prob_normal:.2%}")

# Probability of "extreme" (0-2 or 8-10 messages)
prob_extreme = compute_event_probability(
    lambda x: not is_in_interval(x, 3, 7),
    small_space
)

print(f"Probability of extreme (<3 or >7 messages): {prob_extreme:.2%}")